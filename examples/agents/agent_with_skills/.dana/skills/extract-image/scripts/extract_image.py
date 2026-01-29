from loguru import logger

logger.disable("aicapture")

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource
from aicapture import VisionParser
import argparse


class FileProcessorResource(BaseResource):
    def __init__(self, resource_id: str, **kwargs):
        super().__init__(resource_id=resource_id, **kwargs)
        self.parser = VisionParser()

    @tool_use
    async def process_image(self, image_path: str, prompt: str | None = None) -> dict:
        """
        Process an image file asynchronously and return structured content.

        Args:
            image_path (str): Path to the image file
            prompt (str | None): Prompt to use for the image processing

        Returns:
            dict: Structured content following the same schema as PDF processing
        """
        old_prompt = self.parser.prompt
        self.parser.prompt = prompt
        result = await self.parser.process_image_async(image_path)
        self.parser.prompt = old_prompt
        return result


async def main():
    parser = argparse.ArgumentParser(
        description="Extract and analyze images for Dana agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--fp", type=str, help="Path to image or PDF file")
    parser.add_argument("--prompt", type=str, help="Prompt describing what to extract from the image")

    args = parser.parse_args()

    processor = FileProcessorResource(resource_id="image_processor")
    result = await processor.process_image(image_path=args.fp, prompt=args.prompt)
    content = ""
    for page in result["file_object"]["pages"]:
        content += f"\n===== Page: {page['page_number']} =====\n\n"
        content += page["page_content"]
        content += "\n\n"
    print(content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
