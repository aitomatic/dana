"""Test the MCP SSE Transport implementation."""

import asyncio
import multiprocessing
import time
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import sys

import pytest

from opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport import MCPSSETransport


class TestMCPSSETransport(unittest.TestCase):
    """Test the MCP SSE Transport class - fast unit tests."""

    def test_transport_initialization(self):
        """Test basic transport initialization."""
        transport = MCPSSETransport(
            url="http://localhost:8881/sse",
            timeout=10.0,
            sse_read_timeout=30.0
        )
        
        self.assertEqual(transport.url, "http://localhost:8881/sse")
        self.assertEqual(transport.timeout, 10.0)
        self.assertEqual(transport.sse_read_timeout, 30.0)
        self.assertFalse(transport.is_connected)
        
    def test_server_info_property(self):
        """Test server info property returns correct structure."""
        transport = MCPSSETransport(url="http://test.com/sse")
        
        server_info = transport.server_info
        
        self.assertIsInstance(server_info, dict)
        self.assertIn("url", server_info)
        self.assertIn("connected", server_info)
        self.assertIn("tools_count", server_info)
        self.assertIn("resources_count", server_info)
        self.assertIn("prompts_count", server_info)
        self.assertEqual(server_info["url"], "http://test.com/sse")
        self.assertFalse(server_info["connected"])

    def test_transport_properties(self):
        """Test transport property access."""
        transport = MCPSSETransport(
            url="http://example.com/sse",
            headers={"Authorization": "Bearer token"},
            timeout=20.0
        )
        
        self.assertEqual(transport.url, "http://example.com/sse")
        self.assertEqual(transport.headers, {"Authorization": "Bearer token"})
        self.assertEqual(transport.timeout, 20.0)
        # Caches are initialized as None and populated after connection
        self.assertIsNone(transport._tools_cache)
        self.assertIsNone(transport._resources_cache)
        self.assertIsNone(transport._prompts_cache)

    def test_connection_failure(self):
        """Test connection failure handling."""
        transport = MCPSSETransport(url="http://invalid.url/sse", timeout=0.1)
        
        async def test_fail():
            with self.assertRaises((ConnectionError, TimeoutError)):
                await transport.connect()
                
        asyncio.run(test_fail())


@pytest.mark.deep  
class TestMCPSSETransportMocked(unittest.TestCase):
    """Test MCP SSE Transport with mocked dependencies."""

    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.sse_client')
    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.ClientSession')
    def test_connection_success_mocked(self, mock_session_class, mock_sse_client):
        """Test successful connection flow with mocked dependencies."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=AsyncMock(tools=[]))
        mock_session.list_resources = AsyncMock(return_value=AsyncMock(resources=[]))
        mock_session.list_prompts = AsyncMock(return_value=AsyncMock(prompts=[]))
        
        mock_session_class.return_value = mock_session
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=("read", "write"))
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        
        transport = MCPSSETransport(url="http://test.com/sse")
        
        async def test_connect():
            # Mock the exit stack context manager
            with patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.AsyncExitStack') as mock_exit_stack:
                mock_stack_instance = AsyncMock()
                mock_exit_stack.return_value = mock_stack_instance
                mock_stack_instance.enter_async_context = AsyncMock(side_effect=[
                    ("read", "write"),  # First call for SSE client
                    mock_session      # Second call for ClientSession
                ])
                
                await transport.connect()
                self.assertTrue(transport.is_connected)
                # Check that caches are populated after connection
                self.assertIsNotNone(transport._tools_cache)
                self.assertIsNotNone(transport._resources_cache)
                self.assertIsNotNone(transport._prompts_cache)
                
                await transport.disconnect()
                self.assertFalse(transport.is_connected)
                # Check that caches are cleared after disconnection
                self.assertIsNone(transport._tools_cache)
                self.assertIsNone(transport._resources_cache)
                self.assertIsNone(transport._prompts_cache)
            
        asyncio.run(test_connect())

    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.sse_client')
    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.ClientSession')
    def test_tool_operations_mocked(self, mock_session_class, mock_sse_client):
        """Test tool operations with mocked session."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_session.list_tools = AsyncMock(return_value=AsyncMock(tools=[mock_tool]))
        mock_session.list_resources = AsyncMock(return_value=AsyncMock(resources=[]))
        mock_session.list_prompts = AsyncMock(return_value=AsyncMock(prompts=[]))
        mock_session.call_tool = AsyncMock(return_value=AsyncMock(content="tool result"))
        
        mock_session_class.return_value = mock_session
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=("read", "write"))
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        
        transport = MCPSSETransport(url="http://test.com/sse")
        
        async def test_tools():
            with patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.AsyncExitStack') as mock_exit_stack:
                mock_stack_instance = AsyncMock()
                mock_exit_stack.return_value = mock_stack_instance
                mock_stack_instance.enter_async_context = AsyncMock(side_effect=[
                    ("read", "write"),
                    mock_session
                ])
                
                await transport.connect()
                
                # Test listing tools
                tools = await transport.list_tools()
                self.assertEqual(len(tools), 1)
                self.assertEqual(tools[0].name, "test_tool")
                
                # Test calling tool
                result = await transport.call_tool("test_tool", {"arg": "value"})
                self.assertTrue(result.get("success"))
                self.assertEqual(result.get("content"), "tool result")
                
                await transport.disconnect()
            
        asyncio.run(test_tools())

    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.sse_client')
    @patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.ClientSession')
    def test_context_manager_mocked(self, mock_session_class, mock_sse_client):
        """Test context manager functionality with mocked dependencies."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=AsyncMock(tools=[]))
        mock_session.list_resources = AsyncMock(return_value=AsyncMock(resources=[]))
        mock_session.list_prompts = AsyncMock(return_value=AsyncMock(prompts=[]))
        
        mock_session_class.return_value = mock_session
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=("read", "write"))
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        
        async def test_context_manager():
            with patch('opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.sse_transport.AsyncExitStack') as mock_exit_stack:
                mock_stack_instance = AsyncMock()
                mock_exit_stack.return_value = mock_stack_instance
                mock_stack_instance.enter_async_context = AsyncMock(side_effect=[
                    ("read", "write"),
                    mock_session
                ])
                
                # Test async context manager from base class
                async with MCPSSETransport(url="http://test.com/sse") as transport:
                    self.assertTrue(transport.is_connected)
                    self.assertIsInstance(transport, MCPSSETransport)
                
                # After exiting context, should be disconnected
                self.assertFalse(transport.is_connected)
            
        asyncio.run(test_context_manager())

    def test_connection_check_method(self):
        """Test connection checking without session."""
        transport = MCPSSETransport(url="http://test.com/sse")
        
        async def test_disconnected_calls():
            # Test that methods raise ConnectionError when not connected
            with self.assertRaises(ConnectionError):
                await transport.call_tool("test", {})
                
            with self.assertRaises(ConnectionError):
                await transport.read_resource("test://resource")
                
            with self.assertRaises(ConnectionError):
                await transport.get_prompt("test_prompt")
                
            # List methods should also raise when not connected and no cache
            with self.assertRaises(ConnectionError):
                await transport.list_tools()
                
        asyncio.run(test_disconnected_calls())


@pytest.mark.live
class TestMCPSSETransportLive(unittest.TestCase):
    """Tests requiring external MCP services."""
    
    def test_external_mcp_server_connection(self):
        """Test connection to external MCP server if available."""
        # This would test against a known external MCP server
        # Currently skipped unless --run-live is specified
        self.skipTest("External MCP server test requires live services")


if __name__ == "__main__":
    unittest.main() 