"""
FraudDetectionWorkflow - Orchestrates the fraud detection pipeline.

This workflow coordinates the sequential execution of:
1. DeepExtractor: PDF/Image → Text
2. FieldNormalizer: Text → JSON
3. FraudIndicator: JSON → Fraud Result

The workflow ensures proper data flow between agents and handles errors.
"""

import os
import sys
from typing import Any

# Add parent directory to path for imports
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output


class FraudDetectionWorkflow(BaseWorkflow):
    """
    Workflow for orchestrating fraud detection pipeline.

    This workflow coordinates three specialist agents in sequence:
    1. DeepExtractor: Extracts text from PDF/image files
    2. FieldNormalizer: Converts text to structured JSON
    3. FraudIndicator: Analyzes JSON for fraud patterns

    Data flows through the pipeline: File → Text → JSON → Fraud Result
    """

    def __init__(
        self, workflow_id: str | None = None, deep_extractor_agent=None, field_normalizer_agent=None, fraud_indicator_agent=None, **kwargs
    ):
        """
        Initialize the FraudDetectionWorkflow.

        Args:
            workflow_id: Unique identifier for the workflow
            deep_extractor_agent: DeepExtractor agent instance
            field_normalizer_agent: FieldNormalizer agent instance
            fraud_indicator_agent: FraudIndicator agent instance
            **kwargs: Additional arguments for BaseWorkflow
        """
        super().__init__(workflow_id=workflow_id or "fraud-detection-pipeline", **kwargs)

        # Store agent references
        self.deep_extractor = deep_extractor_agent
        self.field_normalizer = field_normalizer_agent
        self.fraud_indicator = fraud_indicator_agent

    @validate_input(
        file_path={"required": True, "type": str, "min_length": 1},
    )
    @validate_output(
        success={"required": True, "type": bool},
        extracted_text={"required": True, "type": str},
        normalized_data={"required": True, "type": dict},
        fraud_result={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute the fraud detection pipeline.

        Args:
            file_path: Path to the PDF or image file to analyze

        Returns:
            {
                "success": bool,
                "extracted_text": str,
                "normalized_data": dict,
                "fraud_result": dict,
                "pipeline_metadata": dict
            }
        """
        file_path = kwargs.get("file_path")

        print(f"File path: {file_path}")
        # exit()

        if not file_path:
            return {
                "success": False,
                "extracted_text": "",
                "normalized_data": {},
                "fraud_result": {},
                "pipeline_metadata": {"error": "No file_path provided"},
                "error": "file_path parameter is required",
            }

        # Broadcast workflow start
        self.broadcast(
            {
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "start",
                    "message": f"Starting fraud detection pipeline for {file_path}",
                }
            }
        )

        try:
            # ========================================
            # STEP 1: DEEP EXTRACTION (PDF/Image → Text)
            # ========================================
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "extraction",
                        "message": "Step 1/3: Extracting text from document...",
                    }
                }
            )

            if not self.deep_extractor:
                return {
                    "success": False,
                    "extracted_text": "",
                    "normalized_data": {},
                    "fraud_result": {},
                    "pipeline_metadata": {"error": "DeepExtractor agent not available"},
                    "error": "DeepExtractor agent not configured",
                }

            # Call DeepExtractor agent
            extraction_result = self.call_agent(
                agent=self.deep_extractor,
                message=f"Extract text from document {file_path}",
                file_path=file_path,
            )

            if extraction_result.get("error", False):
                return {
                    "success": False,
                    "extracted_text": "",
                    "normalized_data": {},
                    "fraud_result": {},
                    "pipeline_metadata": {"phase": "extraction", "error": extraction_result.get("error")},
                    "error": f"Text extraction failed: {extraction_result.get('error')}",
                }

            extracted_text = extraction_result.get("response", "")

            # ========================================
            # STEP 2: FIELD NORMALIZATION (Text → JSON)
            # ========================================
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "normalization",
                        "message": "Step 2/3: Normalizing text to structured JSON...",
                    }
                }
            )

            if not self.field_normalizer:
                return {
                    "success": False,
                    "extracted_text": extracted_text,
                    "normalized_data": {},
                    "fraud_result": {},
                    "pipeline_metadata": {"error": "FieldNormalizer agent not available"},
                    "error": "FieldNormalizer agent not configured",
                }

            # Call FieldNormalizer agent
            normalization_result = self.call_agent(
                agent=self.field_normalizer, message=f"Normalize extracted text to JSON \n Text to be normalized:\n {extracted_text}"
            )

            if normalization_result.get("error", False):
                return {
                    "success": False,
                    "extracted_text": extracted_text,
                    "normalized_data": {},
                    "fraud_result": {},
                    "pipeline_metadata": {"phase": "normalization", "error": normalization_result.get("error")},
                    "error": f"Text normalization failed: {normalization_result.get('error')}",
                }

            normalized_data = normalization_result.get("response", {})

            # ========================================
            # STEP 3: FRAUD DETECTION (JSON → Fraud Result)
            # ========================================
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "fraud_detection",
                        "message": "Step 3/3: Analyzing data for fraud patterns...",
                    }
                }
            )

            if not self.fraud_indicator:
                return {
                    "success": False,
                    "extracted_text": extracted_text,
                    "normalized_data": normalized_data,
                    "fraud_result": {},
                    "pipeline_metadata": {"error": "FraudIndicator agent not available"},
                    "error": "FraudIndicator agent not configured",
                }

            # Call FraudIndicator agent
            fraud_result = self.call_agent(
                agent=self.fraud_indicator, message=f"Detect fraud patterns in normalized data.\n Normalized data:\n {normalized_data}"
            )

            if fraud_result.get("error", False):
                return {
                    "success": False,
                    "extracted_text": extracted_text,
                    "normalized_data": normalized_data,
                    "fraud_result": {},
                    "pipeline_metadata": {"phase": "fraud_detection", "error": fraud_result.get("error")},
                    "error": f"Fraud detection failed: {fraud_result.get('error')}",
                }

            fraud_analysis = fraud_result.get("response", {})

            # ========================================
            # PIPELINE COMPLETION
            # ========================================
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "complete",
                        "message": f"Fraud detection pipeline completed successfully",
                    }
                }
            )

            # Build comprehensive result
            pipeline_metadata = {
                "workflow_id": self.workflow_id,
                "file_path": file_path,
                "phases_completed": ["extraction", "normalization", "fraud_detection"],
                "success": True,
                "risk_score": fraud_analysis.get("risk_score", 0),
                "fraud_indicators_count": len(fraud_analysis.get("fraud_indicators", [])),
                "anomalies_count": len(fraud_analysis.get("anomalies", [])),
            }

            return {
                "success": True,
                "extracted_text": extracted_text,
                "normalized_data": normalized_data,
                "fraud_result": fraud_analysis,
                "pipeline_metadata": pipeline_metadata,
            }

        except Exception as e:
            # Handle unexpected errors
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "error",
                        "message": f"Pipeline failed with error: {str(e)}",
                    }
                }
            )

            return {
                "success": False,
                "extracted_text": "",
                "normalized_data": {},
                "fraud_result": {},
                "pipeline_metadata": {"workflow_id": self.workflow_id, "error": str(e), "success": False},
                "error": f"Pipeline execution failed: {str(e)}",
            }
