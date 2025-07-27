"""
MCP Adapter: Integration with Anthropic's Model Context Protocol.

This module provides the adapter for executing business rules through
MCP's tool and resource capabilities.
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
import json

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class MCPAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating MCP (Model Context Protocol) with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - Tool registration and execution
    - Resource management
    - Protocol-based communication
    - Context window optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("mcp", config)
        self.capabilities = [
            "tool_execution",
            "resource_management",
            "protocol_communication",
            "context_optimization",
            "tool_discovery",
            "resource_access"
        ]
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.mcp_server_url = config.get("server_url", "http://localhost:8000")
        
    async def connect(self) -> None:
        """Connect to MCP server and discover available tools/resources."""
        try:
            # In a real implementation, this would connect to an actual MCP server
            # For now, we'll simulate the connection
            
            # Discover available tools
            await self._discover_tools()
            
            # Discover available resources
            await self._discover_resources()
            
            self.is_connected = True
            logger.info("MCP adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect MCP adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            # Clear cached tools and resources
            self.tools.clear()
            self.resources.clear()
            
            self.is_connected = False
            logger.info("MCP adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting MCP adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using MCP.
        
        Supported actions:
        - execute_tool: Execute an MCP tool
        - access_resource: Access an MCP resource
        - list_tools: List available tools
        - list_resources: List available resources
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "execute_tool":
                return await self._execute_tool(params, context)
            elif action_type == "access_resource":
                return await self._access_resource(params, context)
            elif action_type == "list_tools":
                return await self._list_tools(params)
            elif action_type == "list_resources":
                return await self._list_resources(params)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing MCP action {action_type}: {e}")
            raise
            
    async def _execute_tool(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool."""
        tool_name = params.get("tool_name")
        tool_params = params.get("parameters", {})
        
        # Get tool definition
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
            
        # Validate parameters
        required_params = tool.get("required_parameters", [])
        for param in required_params:
            if param not in tool_params and param not in context:
                raise ValueError(f"Missing required parameter: {param}")
                
        # Merge context and explicit parameters
        merged_params = {**context, **tool_params}
        
        # Execute tool (simulated for now)
        result = await self._simulate_tool_execution(tool_name, merged_params)
        
        return {
            "tool_name": tool_name,
            "parameters": merged_params,
            "result": result,
            "execution_time": 0.1  # Simulated execution time
        }
        
    async def _access_resource(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Access an MCP resource."""
        resource_name = params.get("resource_name")
        operation = params.get("operation", "read")
        
        # Get resource definition
        resource = self.resources.get(resource_name)
        if not resource:
            raise ValueError(f"Resource not found: {resource_name}")
            
        # Check permissions
        allowed_operations = resource.get("allowed_operations", ["read"])
        if operation not in allowed_operations:
            raise ValueError(f"Operation {operation} not allowed for resource {resource_name}")
            
        # Access resource (simulated for now)
        result = await self._simulate_resource_access(resource_name, operation, params)
        
        return {
            "resource_name": resource_name,
            "operation": operation,
            "result": result,
            "access_time": 0.05  # Simulated access time
        }
        
    async def _list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available MCP tools."""
        category_filter = params.get("category")
        
        tools_list = []
        for name, tool in self.tools.items():
            if category_filter and tool.get("category") != category_filter:
                continue
                
            tools_list.append({
                "name": name,
                "description": tool.get("description", ""),
                "category": tool.get("category", "general"),
                "parameters": tool.get("parameters", [])
            })
            
        return {
            "tools": tools_list,
            "total_count": len(tools_list),
            "filtered_by": category_filter
        }
        
    async def _list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available MCP resources."""
        type_filter = params.get("type")
        
        resources_list = []
        for name, resource in self.resources.items():
            if type_filter and resource.get("type") != type_filter:
                continue
                
            resources_list.append({
                "name": name,
                "description": resource.get("description", ""),
                "type": resource.get("type", "data"),
                "allowed_operations": resource.get("allowed_operations", ["read"])
            })
            
        return {
            "resources": resources_list,
            "total_count": len(resources_list),
            "filtered_by": type_filter
        }
        
    async def _discover_tools(self) -> None:
        """Discover available tools from MCP server."""
        # In a real implementation, this would query the MCP server
        # For now, we'll register some mock tools
        
        self.tools = {
            "calculator": {
                "description": "Perform mathematical calculations",
                "category": "math",
                "parameters": ["expression"],
                "required_parameters": ["expression"]
            },
            "web_search": {
                "description": "Search the web for information",
                "category": "search",
                "parameters": ["query", "limit"],
                "required_parameters": ["query"]
            },
            "file_reader": {
                "description": "Read contents of a file",
                "category": "file",
                "parameters": ["path", "encoding"],
                "required_parameters": ["path"]
            },
            "data_transformer": {
                "description": "Transform data between formats",
                "category": "data",
                "parameters": ["input_data", "from_format", "to_format"],
                "required_parameters": ["input_data", "from_format", "to_format"]
            }
        }
        
        logger.info(f"Discovered {len(self.tools)} MCP tools")
        
    async def _discover_resources(self) -> None:
        """Discover available resources from MCP server."""
        # In a real implementation, this would query the MCP server
        # For now, we'll register some mock resources
        
        self.resources = {
            "knowledge_base": {
                "description": "Company knowledge base",
                "type": "database",
                "allowed_operations": ["read", "query"]
            },
            "config_store": {
                "description": "Configuration storage",
                "type": "config",
                "allowed_operations": ["read", "write"]
            },
            "cache": {
                "description": "Temporary data cache",
                "type": "cache",
                "allowed_operations": ["read", "write", "delete"]
            },
            "api_endpoints": {
                "description": "Available API endpoints",
                "type": "api",
                "allowed_operations": ["read", "invoke"]
            }
        }
        
        logger.info(f"Discovered {len(self.resources)} MCP resources")
        
    async def _simulate_tool_execution(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Simulate tool execution for demonstration."""
        if tool_name == "calculator":
            expression = params.get("expression", "")
            try:
                return {"result": eval(expression)}
            except:
                return {"error": "Invalid expression"}
                
        elif tool_name == "web_search":
            query = params.get("query", "")
            limit = params.get("limit", 10)
            return {
                "results": [
                    {"title": f"Result {i+1} for {query}", "url": f"https://example.com/{i}"}
                    for i in range(min(limit, 3))
                ]
            }
            
        elif tool_name == "file_reader":
            path = params.get("path", "")
            return {"content": f"Mock content of file: {path}"}
            
        elif tool_name == "data_transformer":
            input_data = params.get("input_data", "")
            from_format = params.get("from_format", "")
            to_format = params.get("to_format", "")
            return {
                "transformed_data": f"Data transformed from {from_format} to {to_format}",
                "original_length": len(str(input_data))
            }
            
        return {"status": "executed"}
        
    async def _simulate_resource_access(self, resource_name: str, operation: str, params: Dict[str, Any]) -> Any:
        """Simulate resource access for demonstration."""
        if resource_name == "knowledge_base":
            if operation == "read":
                return {"entries": ["Entry 1", "Entry 2", "Entry 3"]}
            elif operation == "query":
                query = params.get("query", "")
                return {"results": [f"Result for query: {query}"]}
                
        elif resource_name == "config_store":
            if operation == "read":
                key = params.get("key", "default")
                return {"value": f"Config value for {key}"}
            elif operation == "write":
                key = params.get("key", "")
                value = params.get("value", "")
                return {"status": "written", "key": key}
                
        elif resource_name == "cache":
            if operation == "read":
                key = params.get("key", "")
                return {"value": f"Cached value for {key}", "hit": True}
            elif operation == "write":
                key = params.get("key", "")
                value = params.get("value", "")
                return {"status": "cached", "key": key}
            elif operation == "delete":
                key = params.get("key", "")
                return {"status": "deleted", "key": key}
                
        return {"status": "accessed"}
        
    def register_tool(self, name: str, definition: Dict[str, Any]) -> None:
        """Register a custom tool."""
        self.tools[name] = definition
        logger.info(f"Registered MCP tool: {name}")
        
    def register_resource(self, name: str, definition: Dict[str, Any]) -> None:
        """Register a custom resource."""
        self.resources[name] = definition
        logger.info(f"Registered MCP resource: {name}")
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP adapter."""
        health_status = await super().health_check()
        
        # Add MCP-specific metrics
        health_status.update({
            "server_url": self.mcp_server_url,
            "tools_available": len(self.tools),
            "resources_available": len(self.resources),
            "tool_categories": list(set(t.get("category", "general") for t in self.tools.values())),
            "resource_types": list(set(r.get("type", "data") for r in self.resources.values()))
        })
        
        return health_status