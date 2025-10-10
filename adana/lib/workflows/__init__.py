"""
Example workflow implementations for the Adana framework.

This module provides example workflows that demonstrate how to create
and use workflows with agents.
"""

from .google_lookup import GoogleLookupWorkflow

google_lookup_workflow = GoogleLookupWorkflow(workflow_id="google-lookup")

__all__ = ["GoogleLookupWorkflow", "google_lookup_workflow"]
