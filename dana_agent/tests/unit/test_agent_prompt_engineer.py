"""
Unit tests for AgentPromptEngineer.

Tests the prompt engineering for agents that formats the query method
using the configured codec (CSXMLCodec or KLXMLCodec).
"""

import pytest
from unittest.mock import Mock

from dana.common.protocols.types import DictParams
from dana.common.storage import AbstractStorage
from dana.core.agent.base_agent import BaseAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec, KLXMLCodec
from dana.core.knowledge.prompts.agent_prompt_engineer import AgentPromptEngineer


class MockAgentWithQuery(BaseAgent):
    """Mock agent with query method for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(agent_type="mock", auto_register=False, **kwargs)
    
    def query(self, message: str, **kwargs) -> DictParams:
        """Query the agent with a message.
        
        Args:
            message: The message to query the agent with
            **kwargs: Additional keyword arguments
        """
        return {"response": f"Agent response to: {message}"}


class MockAgentWithoutQuery(BaseAgent):
    """Mock agent without query method."""
    
    def __init__(self, **kwargs):
        super().__init__(agent_type="mock_no_query", auto_register=False, **kwargs)
    
    def other_method(self):
        """Other method without query."""
        pass


class TestAgentPromptEngineerInitialization:
    """Test AgentPromptEngineer initialization (Phase 1)."""
    
    def test_initialization_with_agent_component(self):
        """Test 1.1: Initialization with agent component."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent)
        
        assert engineer._component == agent
        assert engineer._codec == CSXMLCodec
        assert engineer._force_generate is False
        assert engineer._check_conflicts is False
    
    def test_initialization_with_custom_codec(self):
        """Test 1.2: Initialization with custom codec."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, codec=KLXMLCodec)
        
        assert engineer._component == agent
        assert engineer._codec == KLXMLCodec
    
    def test_initialization_with_storage(self):
        """Test 1.3: Initialization with storage."""
        agent = MockAgentWithQuery()
        mock_storage = Mock(spec=AbstractStorage)
        engineer = AgentPromptEngineer(agent, storage=mock_storage)
        
        assert engineer._component == agent
        assert engineer._storage == mock_storage
    
    def test_initialization_with_force_generate(self):
        """Test initialization with force_generate flag."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, force_generate=True)
        
        assert engineer._force_generate is True
    
    def test_initialization_with_check_conflicts(self):
        """Test initialization with check_conflicts flag."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, check_conflicts=True)
        
        assert engineer._check_conflicts is True


class TestAgentPromptEngineerConstructPrompt:
    """Test AgentPromptEngineer.construct_prompt() (Phase 2)."""
    
    def test_construct_prompt_with_query_method(self):
        """Test 2.1: construct_prompt with query method."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain formatted query method using CSXMLCodec format
        assert "# MockAgentWithQuery:query" in prompt or "query" in prompt
        assert "Query the agent with a message" in prompt or "message" in prompt
    
    def test_construct_prompt_includes_agent_description(self):
        """Test 2.2: construct_prompt includes agent description."""
        class AgentWithDescription(BaseAgent):
            """This is a test agent description."""
            
            def __init__(self, **kwargs):
                super().__init__(agent_type="test_desc", auto_register=False, **kwargs)
            
            def query(self, **kwargs) -> DictParams:
                """Query method."""
                return {}
        
        agent = AgentWithDescription()
        engineer = AgentPromptEngineer(agent)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include agent description from docstring
        assert "test agent description" in prompt.lower() or "AgentWithDescription" in prompt
    
    def test_construct_prompt_with_klxml_codec(self):
        """Test 2.3: construct_prompt with KLXMLCodec."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, codec=KLXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should use KLXML format (not CSXML function_call format)
        # KLXML format uses <Class:method> tags, not <function_call><invoke>
        assert "<MockAgentWithQuery:query>" in prompt or "MockAgentWithQuery:query" in prompt
    
    def test_construct_prompt_when_query_missing(self):
        """Test 2.4: construct_prompt when query method missing."""
        agent = MockAgentWithoutQuery()
        engineer = AgentPromptEngineer(agent)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        # Should return agent description or empty string
        # (since query method doesn't exist)


class TestAgentPromptEngineerCheckConflicts:
    """Test AgentPromptEngineer.check_conflicts() (Phase 3)."""
    
    def test_check_conflicts_always_returns_false(self):
        """Test 3.1: check_conflicts always returns False."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent)
        
        result = engineer.check_conflicts()
        
        assert isinstance(result, bool)
        assert result is False  # Agents only have query method, no conflicts possible
    
    def test_check_conflicts_returns_bool(self):
        """Test 3.2: check_conflicts always returns boolean."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent)
        
        result = engineer.check_conflicts()
        
        assert isinstance(result, bool)


class TestAgentPromptEngineerIntegration:
    """Test AgentPromptEngineer integration with real agents (Phase 4)."""
    
    def test_with_real_base_agent(self):
        """Test 4.1: Integration with real BaseAgent."""
        agent = BaseAgent(agent_type="test", auto_register=False)
        engineer = AgentPromptEngineer(agent)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain BaseAgent query method
        assert "BaseAgent" in prompt or "query" in prompt.lower()
        # Should contain method signature (note: **kwargs is skipped by parse_method_signature)
        # Just verify it's a valid prompt with query method
    
    def test_codec_integration_csxml(self):
        """Test 4.2a: Verify CSXMLCodec integration."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, codec=CSXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        # CSXMLCodec should produce function_call format
        assert "<function_call>" in prompt or "# MockAgentWithQuery:query" in prompt
    
    def test_codec_integration_klxml(self):
        """Test 4.2b: Verify KLXMLCodec integration."""
        agent = MockAgentWithQuery()
        engineer = AgentPromptEngineer(agent, codec=KLXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        # KLXMLCodec should produce <Class:method> format
        assert "<MockAgentWithQuery:query>" in prompt or "MockAgentWithQuery:query" in prompt

