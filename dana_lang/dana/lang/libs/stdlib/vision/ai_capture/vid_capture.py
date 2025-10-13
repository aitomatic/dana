"""
Simple video capture module for extracting frames from videos.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from .cache import FileCache, HashUtils, S3Cache, TwoLayerCache

# Fix circular import by importing directly from vision_models
from .vision_models import VisionModel, create_default_vision_model


@dataclass
class VideoConfig:
    """Configuration for video processing."""

    max_duration_seconds: int = 30
    frame_rate: int = 2  # Frames per second to extract
    supported_formats: tuple = (".mp4", ".avi", ".mov", ".mkv")
    target_frame_size: tuple = (768, 768)  # Target size for resized frames
    resize_frames: bool = True
    cache_dir: str | None = None  # Directory for caching results
    cloud_bucket: str | None = None  # S3 bucket for cloud caching


class VideoValidationError(Exception):
    """Raised when video validation fails."""


class VidCapture:
    """
    Simple utility for extracting frames from video files and analyzing them.

    Features:
    - Extracts frames from video files at specified rates
    - Analyzes frames with a vision model
    - Provides caching to avoid re-processing the same video with the same prompt

    The cache key is generated based on:
    - The SHA-256 hash of the video file
    - The SHA-256 hash of the prompt
    - The frame extraction rate

    Both local file caching and S3 cloud caching are supported.
    """

    def __init__(
        self,
        config: VideoConfig | None = None,
        vision_model: VisionModel | None = None,
        invalidate_cache: bool = False,
    ):
        """
        Initialize VideoCapture with configuration.

        Args:
            config: Configuration for video processing
            vision_model: Vision model for image analysis (created if None)
            invalidate_cache: If True, bypass cache for reads
        """
        self.config = config or VideoConfig()
        self.vision_model = vision_model or create_default_vision_model()
        self.invalidate_cache = invalidate_cache

        # Initialize file cache
        cache_dir = self.config.cache_dir or "tmp/.vid_capture_cache"
        file_cache = FileCache(cache_dir=cache_dir)

        # Initialize S3 cache if bucket is provided
        s3_cache = None
        if self.config.cloud_bucket:
            s3_cache = S3Cache(bucket=self.config.cloud_bucket, prefix="production/video_results")

        # Set up two-layer cache
        self.cache = TwoLayerCache(file_cache=file_cache, s3_cache=s3_cache, invalidate_cache=invalidate_cache)

    def _validate_video(self, video_path: str) -> None:
        """
        Validate video file format and duration.

        Args:
            video_path: Path to video file

        Raises:
            VideoValidationError: If validation fails
        """
        if not any(video_path.lower().endswith(fmt) for fmt in self.config.supported_formats):
            raise VideoValidationError(f"Unsupported video format. Supported formats: {self.config.supported_formats}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoValidationError("Failed to open video file")

        # Check duration
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        if duration > self.config.max_duration_seconds:
            raise VideoValidationError(f"Video duration ({duration:.1f}s) exceeds maximum allowed ({self.config.max_duration_seconds}s)")

        cap.release()

    def _optimize_frame(self, frame: np.ndarray) -> Image.Image:
        """
        Optimize video frame for processing.

        Args:
            frame: OpenCV frame (BGR format)

        Returns:
            PIL Image optimized for processing
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        # Resize if needed while maintaining aspect ratio
        if self.config.resize_frames:
            width, height = image.size
            if width > self.config.target_frame_size[0] or height > self.config.target_frame_size[1]:
                scale = min(
                    self.config.target_frame_size[0] / width,
                    self.config.target_frame_size[1] / height,
                )
                new_size = (int(width * scale), int(height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def extract_frames(self, video_path: str) -> tuple[list[Image.Image], float]:
        """
        Extract frames from video at specified intervals.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (list of frames, frame interval in seconds)
        """
        # Validate the video first
        self._validate_video(video_path)

        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_file}")

        cap = cv2.VideoCapture(str(video_file))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # Calculate frame interval based on desired frame rate
        frame_interval = 1.0 / self.config.frame_rate
        frames = []

        # Calculate how many frames to extract
        num_frames_to_extract = min(
            int(duration * self.config.frame_rate),
            int(self.config.max_duration_seconds * self.config.frame_rate),
        )

        print(f"Extracting {num_frames_to_extract} frames at {self.config.frame_rate} fps from video with duration {duration:.1f}s")

        for frame_idx in range(num_frames_to_extract):
            # Calculate the frame position
            frame_position = int(frame_idx * frame_interval * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

            ret, frame = cap.read()
            if not ret:
                break

            # Optimize and store frame
            pil_frame = self._optimize_frame(frame)
            frames.append(pil_frame)

        cap.release()
        return frames, frame_interval

    async def capture_async(self, prompt: str, images: list[Image.Image], **kwargs: Any) -> str:
        """
        Extract knowledge from a list of images using a vision model.

        Args:
            prompt: Instruction prompt for the vision model
            images: List of images to analyze
            **kwargs: Additional parameters to pass to the vision model

        Returns:
            String containing the extracted knowledge
        """
        if not images:
            raise ValueError("No images provided for analysis")

        print(f"Analyzing {len(images)} images with vision model")

        # Process the images with the vision model
        result = await self.vision_model.process_image_async(image=images, prompt=prompt, **kwargs)

        return result

    def capture(self, prompt: str, images: list[Image.Image], **kwargs: Any) -> str:
        """
        Synchronous wrapper for capture_async.

        Args:
            prompt: Instruction prompt for the vision model
            images: List of images to analyze
            **kwargs: Additional parameters to pass to the vision model

        Returns:
            String containing the extracted knowledge
        """
        return asyncio.run(self.capture_async(prompt, images, **kwargs))

    def _get_cache_key(self, video_path: str, prompt: str) -> str | None:
        """
        Generate a cache key from video file hash, prompt, and frame rate.

        Args:
            video_path: Path to the video file
            prompt: Instruction prompt for the vision model

        Returns:
            Cache key or None if generation fails
        """
        try:
            # Calculate file hash
            file_hash = HashUtils.calculate_file_hash(video_path)

            # Create prompt hash
            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

            # Create cache key with frame rate
            return f"{file_hash}_{prompt_hash}_{self.config.frame_rate}"
        except Exception as e:
            print(f"Failed to generate cache key: {str(e)}")
            return None

    async def _get_from_cache_async(self, cache_key: str) -> str | None:
        """
        Try to get a result from the cache asynchronously.

        Args:
            cache_key: The cache key to look up

        Returns:
            Cached result or None if not found
        """
        if not cache_key or self.invalidate_cache:
            return None

        try:
            cached_result = await self.cache.get(cache_key)
            if cached_result and "result" in cached_result:
                print(f"Using cached result with key: {cache_key}")
                return cached_result.get("result", None)  # type: ignore
        except Exception as e:
            print(f"Cache lookup failed: {str(e)}")

        return None

    def _get_from_cache(self, cache_key: str) -> str | None:
        """
        Try to get a result from the cache (synchronous version).

        Args:
            cache_key: The cache key to look up

        Returns:
            Cached result or None if not found
        """
        return asyncio.run(self._get_from_cache_async(cache_key))

    async def _save_to_cache_async(self, cache_key: str, result: str) -> None:
        """
        Save a result to the cache asynchronously.

        Args:
            cache_key: The cache key to use
            result: The result to cache
        """
        try:
            await self.cache.set(cache_key, {"result": result})
            print(f"Saved result to cache with key: {cache_key}")
        except Exception as e:
            print(f"Failed to save to cache: {str(e)}")

    def _save_to_cache(self, cache_key: str, result: str) -> None:
        """
        Save a result to the cache (synchronous version).

        Args:
            cache_key: The cache key to use
            result: The result to cache
        """
        asyncio.run(self._save_to_cache_async(cache_key, result))

    def process_video(self, video_path: str, prompt: str, **kwargs: Any) -> str:
        """
        Extract frames from a video and analyze them with a vision model.

        Args:
            video_path: Path to the video file
            prompt: Instruction prompt for the vision model
            **kwargs: Additional parameters to pass to the vision model

        Returns:
            String containing the extracted knowledge from the video frames
        """
        # Check cache first
        cache_key = self._get_cache_key(video_path, prompt)
        cached_result = self._get_from_cache(cache_key)  # type: ignore
        if cached_result:
            return cached_result

        # Cache miss or invalidation - process the video
        # Extract frames from the video
        frames, _ = self.extract_frames(video_path)

        if not frames:
            raise ValueError(f"No frames could be extracted from {video_path}")

        result = self.capture(prompt, frames, **kwargs)

        # Store in cache
        self._save_to_cache(cache_key, result)  # type: ignore

        return result

    async def process_video_async(self, video_path: str, prompt: str, **kwargs: Any) -> str:
        """
        Asynchronous wrapper for process_video.

        Checks cache first, processes video if not in cache, and stores result.

        Args:
            video_path: Path to the video file
            prompt: Instruction prompt for the vision model
            **kwargs: Additional parameters to pass to the vision model

        Returns:
            String containing the extracted knowledge from the video frames
        """
        # Check cache first
        cache_key = self._get_cache_key(video_path, prompt)
        cached_result = await self._get_from_cache_async(cache_key)  # type: ignore
        if cached_result:
            return cached_result

        # Cache miss or invalidation - process the video
        frames, _ = self.extract_frames(video_path)

        if not frames:
            raise ValueError(f"No frames could be extracted from {video_path}")

        result = await self.capture_async(prompt, frames, **kwargs)

        # Store in cache
        await self._save_to_cache_async(cache_key, result)  # type: ignore

        return result

    @classmethod
    def analyze_video(cls, video_path: str) -> dict:
        """
        Analyze a video and return video metadata.

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary containing video metadata (resolution, duration, fps, etc.)
            or error information if analysis fails.
        """
        # Check if file exists
        if not Path(video_path).exists():
            return {
                "status": "error",
                "message": f"Video file not found: {video_path}",
            }

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoValidationError("Failed to open video file")

            # Extract metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))

            # Convert codec integer to string representation
            codec = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])

            return {
                "status": "success",
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "codec": codec,
            }
        except VideoValidationError as e:
            return {
                "status": "error",
                "message": str(e),
            }
        except cv2.error as e:
            return {
                "status": "error",
                "message": f"OpenCV error: {str(e)}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
            }
        finally:
            if "cap" in locals() and cap is not None:
                cap.release()
