import asyncio
import os
from typing import Any, Dict, List, Optional, Union, cast

from loguru import logger


def get_s3_client() -> Any:
    import boto3  # type: ignore

    if os.getenv("USE_MINIO", "false").lower() == "true":
        return boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            config=boto3.session.Config(signature_version="s3v4"),
        )
    else:
        return boto3.client("s3")


def ensure_bucket_exists(bucket_name: str) -> None:
    s3_client = get_s3_client()
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        # The bucket does not exist or you have no access.
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} created successfully")
        except Exception as e:
            logger.error(f"Could not create bucket {bucket_name}: {e}")
            raise


def get_default_bucket() -> str:
    return os.getenv("DXA_DATA_BUCKET", "test-bucket-local")


# Create default buckets when using Minio
if os.getenv("USE_MINIO", "false").lower() == "true":
    # Get bucket name from environment or use a default
    default_bucket = os.getenv("DXA_DATA_BUCKET", "test-bucket-local")
    ensure_bucket_exists(default_bucket)
    logger.info("Using MinIO for vision cache")


async def list_s3_files(bucket: str, prefix: str) -> List[str]:
    s3_client = get_s3_client()
    paginator = s3_client.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                if "/images/" in str(obj["Key"]):
                    continue
                files.append(obj["Key"])
    if prefix in files:
        files.remove(prefix)
    return files


async def upload_file_to_s3_async(
    bucket: str, file_or_data: Union[str, bytes], s3_path: str
) -> None:
    """Async version of upload_file_to_s3.

    Args:
        bucket: S3 bucket name
        file_or_data: Either a file path (str) or bytes data to upload
        s3_path: S3 key to upload to
    """
    try:
        loop = asyncio.get_running_loop()
        s3_client = get_s3_client()

        if isinstance(file_or_data, str):
            # If it's a file path, use upload_file
            logger.info(f"Uploading file {file_or_data} to {bucket}/{s3_path}")
            await loop.run_in_executor(
                None, s3_client.upload_file, file_or_data, bucket, s3_path
            )
        else:
            # If it's bytes, use put_object
            logger.info(f"Uploading data to {bucket}/{s3_path}")
            await loop.run_in_executor(
                None,
                lambda: s3_client.put_object(
                    Bucket=bucket, Key=s3_path, Body=file_or_data
                ),
            )
        logger.info("Uploaded successfully")
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")


async def delete_file_from_s3_async(bucket: str, key: str) -> None:
    """Async delete file from S3."""
    try:
        loop = asyncio.get_running_loop()
        s3_client = get_s3_client()
        await loop.run_in_executor(
            None, lambda: s3_client.delete_object(Bucket=bucket, Key=key)
        )
    except Exception as e:
        logger.error(f"Error deleting from S3: {e}")


async def get_file_from_s3_async(bucket: str, key: str) -> Optional[bytes]:
    """Async get file content from S3.

    Args:
        bucket: S3 bucket name
        key: S3 key/path to the file

    Returns:
        File contents as bytes if successful, None otherwise
    """
    try:
        loop = asyncio.get_running_loop()
        s3_client = get_s3_client()
        response = await loop.run_in_executor(
            None, lambda: s3_client.get_object(Bucket=bucket, Key=key)
        )
        return await loop.run_in_executor(None, lambda: response["Body"].read())
    except Exception as e:
        logger.debug(f"Could not get file from S3: {str(e)}")
        return None


async def download_file_from_s3_async(
    bucket: str, s3_key: str, local_path: str
) -> bool:
    """Download a file from S3 to a local path asynchronously.

    Args:
        bucket: S3 bucket name
        s3_key: S3 key/path to the file
        local_path: Local path to save the file to

    Returns:
        True if successful, False otherwise
    """
    try:
        loop = asyncio.get_running_loop()
        s3_client = get_s3_client()

        # Use run_in_executor to make the blocking download_file call non-blocking
        await loop.run_in_executor(
            None, lambda: s3_client.download_file(bucket, s3_key, local_path)
        )
        return True
    except Exception as e:
        logger.error(f"Error downloading {s3_key} from S3: {str(e)}")
        return False


async def list_objects_from_s3_async(bucket: str, prefix: str) -> List[Dict[str, Any]]:
    """List objects in an S3 bucket with a given prefix asynchronously.

    Args:
        bucket: S3 bucket name
        prefix: S3 prefix to list objects from

    Returns:
        List of object dictionaries containing Key, Size, etc.
    """
    try:
        loop = asyncio.get_running_loop()
        s3_client = get_s3_client()

        # Use run_in_executor to make the blocking list_objects_v2 call non-blocking
        response = await loop.run_in_executor(
            None, lambda: s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        )

        # Explicitly handle the typing
        if "Contents" in response and isinstance(response["Contents"], list):
            # Cast contents to the expected type
            contents: List[Dict[str, Any]] = cast(
                List[Dict[str, Any]], response["Contents"]
            )
            return contents

        # Return empty list if no contents
        return []
    except Exception as e:
        logger.error(f"Error listing objects from S3 with prefix {prefix}: {str(e)}")
        return []
