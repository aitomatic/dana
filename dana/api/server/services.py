import logging


from dana.core.lang.dana_sandbox import DanaSandbox

from ..core.schemas import RunNAFileRequest, RunNAFileResponse

# Set up logging
logger = logging.getLogger(__name__)


def run_na_file_service(request: RunNAFileRequest):
    """
    Run a Dana (.na) file and return the result.

    This service executes a Dana file and returns the output or any errors.
    """
    try:
        logger.info(f"Running Dana file: {request.file_path}")

        # Create a new DanaSandbox instance
        sandbox = DanaSandbox()

        # Execute the file
        result = sandbox.execute_file(request.file_path, input_data=request.input)

        return RunNAFileResponse(
            success=True, output=result.get("output", ""), result=result.get("result"), final_context=result.get("context", {})
        )

    except Exception as e:
        logger.error(f"Error running Dana file {request.file_path}: {e}")
        return RunNAFileResponse(success=False, error=str(e))
