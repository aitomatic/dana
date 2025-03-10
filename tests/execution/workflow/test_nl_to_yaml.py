"""Test natural language to YAML workflow implementation."""

import unittest
from unittest.mock import patch, AsyncMock
import asyncio

from dxa.execution.workflow.workflow_factory import WorkflowFactory
from dxa.execution import Workflow
from dxa.execution import Objective


class TestNLToYAML(unittest.TestCase):
    """Test natural language to YAML workflow implementation."""

    def setUp(self):
        """Set up test data."""
        self.natural_language = """
        When equipment issues come up in the fab, operators usually start by looking at the basic stuff - 
        power, pressure, those kinds of readings. If anything looks off, they'll want to check 
        the maintenance history and see if someone's worked on it recently. Sometimes the logs will show 
        some warnings that help point to what's wrong. If the basic checks don't show anything obvious, 
        they'll need to dig deeper into the process data and maybe check if sensors are reading correctly. 
        It's important to document everything as you go. If they can't figure it out quickly, they'll need 
        to call in the technical team and maybe shut things down temporarily while they investigate. 
        The key is to be thorough but also work quickly to minimize downtime.
        """
        
        self.organized_natural_language = """
        Root: Troubleshooting Equipment Issues in the Fab

        1. Initial Checks
           - Examine basic parameters such as power and pressure readings
           - Identify any abnormalities in the readings

        2. Review Maintenance History
           - Check if the equipment has been serviced or repaired recently
           - Look for any warnings or errors in the logs that might indicate the source of the issue

        3. Advanced Checks
           - If initial checks and maintenance history review do not point to a clear issue, 
             investigate the process data
           - Verify if sensors are functioning and providing accurate readings

        4. Documentation
           - Keep a record of all observations, checks, and tests conducted during the troubleshooting process

        5. Technical Assistance
           - If the issue remains unresolved after initial and advanced checks, 
             contact the technical team for further investigation
           - Consider temporarily shutting down the equipment to prevent further complications or damage

        6. Efficiency
           - Ensure the troubleshooting process is thorough yet swift to minimize equipment downtime.
        """
        
        self.yaml_content = """
        name: "Troubleshooting Equipment Issues in the Fab"
        description: "Workflow for troubleshooting equipment issues in the fab"
        version: 1.0
        role: "Equipment Technician"
        type: "SEQUENTIAL"
        nodes:
          - id: "INITIAL_CHECKS"
            description: "Perform initial checks on equipment"
            type: "TASK"
          - id: "REVIEW_MAINTENANCE_HISTORY"
            description: "Review the maintenance history of equipment"
            type: "TASK"
          - id: "ADVANCED_CHECKS"
            description: "Perform advanced checks if initial checks and maintenance history review do not 
            point to a clear issue"
            type: "TASK"
          - id: "DOCUMENTATION"
            description: "Document all observations, checks, and tests conducted"
            type: "TASK"
          - id: "TECHNICAL_ASSISTANCE"
            description: "Seek technical assistance if the issue remains unresolved after initial and 
            advanced checks"
            type: "TASK"
          - id: "EFFICIENCY"
            description: "Ensure the troubleshooting process is thorough yet swift"
            type: "TASK"
        prompts:
          INITIAL_CHECKS: |
            Examine basic parameters such as power and pressure readings. 
            Identify and note down any discrepancies in the readings.
          REVIEW_MAINTENANCE_HISTORY: |
            Check if the equipment has been serviced or repaired recently. 
            Look for any warnings or errors in the logs that might indicate the source of the issue.
          ADVANCED_CHECKS: |
            If initial checks and maintenance history review do not point to a clear issue, 
            investigate the process data. Verify if sensors are functioning and providing accurate readings.
          DOCUMENTATION: |
            Keep a record of all observations, checks, and tests conducted during the troubleshooting process.
          TECHNICAL_ASSISTANCE: |
            If the issue remains unresolved after initial and advanced checks, 
            contact the technical team for further investigation. 
            Consider temporarily shutting down the equipment to prevent further complications or damage.
          EFFICIENCY: |
            Ensure the troubleshooting process is thorough yet swift to minimize equipment downtime.
        """

    @patch('dxa.agent.resource.LLMResource')
    def test_nl_to_onl(self, mock_llm_resource):
        """Test nl_to_onl method."""
        # Setup mock
        mock_instance = mock_llm_resource.return_value
        mock_instance.query = AsyncMock(return_value={'content': self.organized_natural_language})
        mock_instance.cleanup = AsyncMock()
        
        # Run the test
        result = asyncio.run(WorkflowFactory.nl_to_onl(self.natural_language))
        
        # Assertions
        self.assertEqual(result, self.organized_natural_language)
        mock_instance.query.assert_called_once()
        mock_instance.cleanup.assert_called_once()

    @patch('dxa.agent.resource.LLMResource')
    def test_onl_to_yaml(self, mock_llm_resource):
        """Test onl_to_yaml method."""
        # Setup mock
        mock_instance = mock_llm_resource.return_value
        mock_instance.query = AsyncMock(return_value={'content': self.yaml_content})
        mock_instance.cleanup = AsyncMock()
        
        # Run the test
        result = asyncio.run(WorkflowFactory.onl_to_yaml(self.organized_natural_language))
        
        # Assertions - strip whitespace for comparison
        self.assertEqual(result.strip(), self.yaml_content.strip())
        mock_instance.query.assert_called_once()
        mock_instance.cleanup.assert_called_once()

    @patch('dxa.execution.workflow.workflow_factory.WorkflowFactory.nl_to_onl')
    @patch('dxa.execution.workflow.workflow_factory.WorkflowFactory.onl_to_yaml')
    @patch('dxa.execution.workflow.workflow_factory.WorkflowFactory.from_yaml')
    def test_nl_to_workflow(self, mock_from_yaml, mock_onl_to_yaml, mock_nl_to_onl):
        """Test nl_to_workflow method."""
        # Setup mocks
        mock_nl_to_onl.return_value = self.organized_natural_language
        mock_onl_to_yaml.return_value = self.yaml_content
        
        mock_workflow = Workflow(objective=Objective("Test workflow"))
        mock_from_yaml.return_value = mock_workflow
        
        # Run the test
        result = asyncio.run(WorkflowFactory.nl_to_workflow(self.natural_language))
        
        # Assertions
        self.assertEqual(result, mock_workflow)
        mock_nl_to_onl.assert_called_once_with(self.natural_language)
        mock_onl_to_yaml.assert_called_once_with(self.organized_natural_language)
        mock_from_yaml.assert_called_once_with(self.yaml_content)

    @patch('dxa.agent.resource.LLMResource')
    def test_nl_to_onl_error_handling(self, mock_llm_resource):
        """Test nl_to_onl error handling."""
        # Setup mock to return an invalid response
        mock_instance = mock_llm_resource.return_value
        mock_instance.query = AsyncMock(return_value={})  # Missing 'content' field
        mock_instance.cleanup = AsyncMock()
        
        # Run the test and check for exception
        with self.assertRaises(ValueError) as context:
            asyncio.run(WorkflowFactory.nl_to_onl(self.natural_language))
        
        self.assertIn("Invalid LLM response", str(context.exception))
        mock_instance.cleanup.assert_called_once()

    @patch('dxa.agent.resource.LLMResource')
    def test_onl_to_yaml_error_handling(self, mock_llm_resource):
        """Test onl_to_yaml error handling."""
        # Setup mock to return an invalid YAML
        mock_instance = mock_llm_resource.return_value
        mock_instance.query = AsyncMock(return_value={'content': 'invalid: yaml: content: -'})
        mock_instance.cleanup = AsyncMock()
        
        # Run the test and check for exception
        with self.assertRaises(ValueError) as context:
            asyncio.run(WorkflowFactory.onl_to_yaml(self.organized_natural_language))
        
        self.assertIn("Generated YAML is invalid", str(context.exception))
        mock_instance.cleanup.assert_called_once()

    @patch('dxa.execution.workflow.workflow_factory.WorkflowFactory.nl_to_onl')
    @patch('dxa.execution.workflow.workflow_factory.WorkflowFactory.onl_to_yaml')
    def test_nl_to_workflow_error_propagation(self, mock_onl_to_yaml, mock_nl_to_onl):
        """Test nl_to_workflow error propagation."""
        # Setup mocks to raise exceptions
        error_message = "Test error"
        mock_nl_to_onl.side_effect = ValueError(error_message)
        
        # Run the test and check for exception
        with self.assertRaises(ValueError) as context:
            asyncio.run(WorkflowFactory.nl_to_workflow(self.natural_language))
        
        self.assertEqual(str(context.exception), error_message)
        mock_nl_to_onl.assert_called_once_with(self.natural_language)
        mock_onl_to_yaml.assert_not_called()

    @patch('dxa.agent.resource.LLMResource')
    def test_integration_nl_to_workflow(self, mock_llm_resource):
        """Test the entire workflow from natural language to workflow creation."""
        # Setup mock
        mock_instance = mock_llm_resource.return_value
        
        # First call to nl_to_onl
        # Second call to onl_to_yaml
        mock_instance.query = AsyncMock(side_effect=[
            {'content': self.organized_natural_language},
            {'content': self.yaml_content}
        ])
        mock_instance.cleanup = AsyncMock()
        
        # Run the test
        workflow = asyncio.run(WorkflowFactory.nl_to_workflow(self.natural_language))
        
        # Assertions
        self.assertIsInstance(workflow, Workflow)
        self.assertEqual(len(workflow.nodes), 8)  # 6 task nodes + START + END
        
        # Verify specific nodes exist
        self.assertIn("INITIAL_CHECKS", workflow.nodes)
        self.assertIn("REVIEW_MAINTENANCE_HISTORY", workflow.nodes)
        self.assertIn("ADVANCED_CHECKS", workflow.nodes)
        self.assertIn("DOCUMENTATION", workflow.nodes)
        self.assertIn("TECHNICAL_ASSISTANCE", workflow.nodes)
        self.assertIn("EFFICIENCY", workflow.nodes)
        
        # Verify the mock was called twice (once for nl_to_onl, once for onl_to_yaml)
        self.assertEqual(mock_instance.query.call_count, 2)
        self.assertEqual(mock_instance.cleanup.call_count, 2)


if __name__ == '__main__':
    unittest.main() 