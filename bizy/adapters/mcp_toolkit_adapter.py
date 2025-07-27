"""
MCP Tool Kit Adapter: Enhanced integration with existing MCP Tool Kit.

This module provides specialized integration with an existing MCP Tool Kit,
demonstrating how the Business Logic Orchestrator adds value without
replacing existing functionality.
"""

from typing import Any, Dict, List, Optional, Set
import logging
import asyncio
import json
from pathlib import Path

from .mcp_adapter import MCPAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class MCPToolKitAdapter(MCPAdapter):
    """
    Enhanced adapter specifically for integrating with existing MCP Tool Kit.
    
    Extends the base MCP adapter with:
    - Discovery of existing tool configurations
    - Business logic enhancement layer
    - Tool composition and chaining
    - Advanced caching and optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize base MCP adapter
        super().__init__(config)
        
        # MCP Tool Kit specific configuration
        self.toolkit_path = Path(config.get("toolkit_path", "/storage/mcp-tool-kit"))
        self.tool_configs: Dict[str, Dict[str, Any]] = {}
        self.tool_chains: Dict[str, List[str]] = {}
        self.business_enhancements: Dict[str, Any] = {}
        
        # Add tool kit specific capabilities
        self.capabilities.extend([
            "tool_composition",
            "business_enhancement",
            "tool_chaining",
            "config_discovery",
            "performance_optimization"
        ])
        
    async def connect(self) -> None:
        """Connect to MCP Tool Kit and discover available tools."""
        try:
            # First connect using base MCP functionality
            await super().connect()
            
            # Discover existing tool configurations
            await self._discover_toolkit_configurations()
            
            # Load business enhancement definitions
            await self._load_business_enhancements()
            
            # Initialize tool composition patterns
            await self._initialize_tool_chains()
            
            logger.info(f"MCP Tool Kit adapter connected with {len(self.tool_configs)} discovered tools")
            
        except Exception as e:
            logger.error(f"Failed to connect MCP Tool Kit adapter: {e}")
            raise
            
    async def _discover_toolkit_configurations(self) -> None:
        """Discover tool configurations from existing MCP Tool Kit."""
        config_paths = [
            self.toolkit_path / "tools.json",
            self.toolkit_path / "config" / "tools.yaml",
            self.toolkit_path / "mcp-config.json"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        if config_path.suffix == '.json':
                            configs = json.load(f)
                        else:
                            # Would use yaml.safe_load in production
                            configs = {}
                            
                    # Process tool configurations
                    for tool_name, tool_config in configs.get("tools", {}).items():
                        self.tool_configs[tool_name] = tool_config
                        
                        # Register with base adapter
                        self.register_tool(tool_name, {
                            "description": tool_config.get("description", ""),
                            "category": tool_config.get("category", "general"),
                            "parameters": tool_config.get("parameters", []),
                            "required_parameters": tool_config.get("required", []),
                            "toolkit_native": True
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
                    
        logger.info(f"Discovered {len(self.tool_configs)} tools from MCP Tool Kit")
        
    async def _load_business_enhancements(self) -> None:
        """Load business logic enhancements for existing tools."""
        enhancements_path = self.toolkit_path / "business_enhancements.json"
        
        if enhancements_path.exists():
            try:
                with open(enhancements_path, 'r') as f:
                    self.business_enhancements = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load business enhancements: {e}")
                
        # Default business enhancements for common patterns
        default_enhancements = {
            "validation": {
                "calculator": {
                    "pre_execution": [
                        {"type": "validate_expression", "params": {"max_length": 100}}
                    ],
                    "post_execution": [
                        {"type": "validate_result", "params": {"min": -1e10, "max": 1e10}}
                    ]
                }
            },
            "caching": {
                "web_search": {
                    "cache_key": ["query", "limit"],
                    "ttl": 3600
                },
                "file_reader": {
                    "cache_key": ["path"],
                    "ttl": 300
                }
            },
            "composition": {
                "enhanced_search": {
                    "tools": ["web_search", "data_transformer"],
                    "flow": "sequential"
                }
            }
        }
        
        # Merge with loaded enhancements
        for category, rules in default_enhancements.items():
            if category not in self.business_enhancements:
                self.business_enhancements[category] = {}
            self.business_enhancements[category].update(rules)
            
    async def _initialize_tool_chains(self) -> None:
        """Initialize tool composition and chaining patterns."""
        # Define common tool chains
        self.tool_chains = {
            "data_processing_pipeline": [
                "file_reader",
                "data_transformer",
                "calculator"
            ],
            "research_workflow": [
                "web_search",
                "data_transformer",
                "file_writer"
            ],
            "analysis_chain": [
                "file_reader",
                "calculator",
                "data_visualizer"
            ]
        }
        
        # Register chains as composite tools
        for chain_name, tool_sequence in self.tool_chains.items():
            self.register_tool(f"chain_{chain_name}", {
                "description": f"Composite tool chain: {' -> '.join(tool_sequence)}",
                "category": "composite",
                "parameters": ["input_data"],
                "tool_sequence": tool_sequence,
                "is_chain": True
            })
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action with business logic enhancements.
        
        Extends base MCP execution with:
        - Pre/post execution validation
        - Business rule application
        - Tool composition
        - Enhanced caching
        """
        action_type = action.action
        
        # Check if this is a tool kit enhanced action
        if action_type == "execute_enhanced_tool":
            return await self._execute_enhanced_tool(action.parameters, context)
        elif action_type == "execute_tool_chain":
            return await self._execute_tool_chain(action.parameters, context)
        elif action_type == "compose_tools":
            return await self._compose_tools(action.parameters, context)
        else:
            # Fall back to base MCP adapter
            return await super()._execute_action(action, context)
            
    async def _execute_enhanced_tool(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with business logic enhancements."""
        tool_name = params.get("tool_name")
        tool_params = params.get("parameters", {})
        
        # Apply pre-execution enhancements
        validation_rules = self.business_enhancements.get("validation", {}).get(tool_name, {})
        
        if "pre_execution" in validation_rules:
            for rule in validation_rules["pre_execution"]:
                if not await self._apply_validation_rule(rule, tool_params):
                    return {
                        "error": f"Pre-execution validation failed: {rule['type']}",
                        "tool_name": tool_name
                    }
                    
        # Check caching
        cache_config = self.business_enhancements.get("caching", {}).get(tool_name, {})
        if cache_config:
            cache_key = self._generate_cache_key(tool_name, tool_params)
            cached_result = self.tool_cache.get(cache_key)
            
            if cached_result and self._is_cache_valid(cached_result, cache_config.get("ttl", 300)):
                return {
                    "tool_name": tool_name,
                    "result": cached_result["result"],
                    "cached": True,
                    "enhanced": True
                }
                
        # Execute base tool
        result = await super()._execute_tool(params, context)
        
        # Apply post-execution enhancements
        if "post_execution" in validation_rules:
            for rule in validation_rules["post_execution"]:
                if not await self._apply_validation_rule(rule, result.get("result", {})):
                    return {
                        "error": f"Post-execution validation failed: {rule['type']}",
                        "tool_name": tool_name,
                        "original_result": result
                    }
                    
        # Cache result if configured
        if cache_config:
            self.tool_cache[cache_key] = {
                "result": result,
                "timestamp": asyncio.get_event_loop().time(),
                "ttl": cache_config.get("ttl", 300)
            }
            
        # Add enhancement metadata
        result["enhanced"] = True
        result["enhancements_applied"] = list(validation_rules.keys())
        
        return result
        
    async def _execute_tool_chain(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined tool chain."""
        chain_name = params.get("chain_name")
        input_data = params.get("input_data")
        
        if chain_name not in self.tool_chains:
            # Check if it's a registered composite tool
            chain_key = chain_name.replace("chain_", "")
            if chain_key not in self.tool_chains:
                return {"error": f"Unknown tool chain: {chain_name}"}
                
            chain_name = chain_key
            
        tool_sequence = self.tool_chains[chain_name]
        results = []
        current_data = input_data
        
        # Execute tools in sequence
        for i, tool_name in enumerate(tool_sequence):
            tool_params = {
                "tool_name": tool_name,
                "parameters": {
                    "input": current_data,
                    "step": i + 1,
                    "total_steps": len(tool_sequence)
                }
            }
            
            # Execute tool
            result = await self._execute_enhanced_tool(tool_params, context)
            
            if "error" in result:
                return {
                    "chain_name": chain_name,
                    "failed_at_step": i + 1,
                    "failed_tool": tool_name,
                    "error": result["error"],
                    "partial_results": results
                }
                
            results.append(result)
            
            # Use output as input for next tool
            current_data = result.get("result", {})
            
        return {
            "chain_name": chain_name,
            "tools_executed": tool_sequence,
            "results": results,
            "final_output": current_data,
            "execution_time": sum(r.get("execution_time", 0) for r in results)
        }
        
    async def _compose_tools(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically compose tools based on business logic."""
        composition_type = params.get("type", "sequential")
        tools = params.get("tools", [])
        
        if composition_type == "sequential":
            # Execute tools in sequence
            return await self._execute_tool_chain({
                "chain_name": "dynamic_composition",
                "input_data": params.get("input_data")
            }, context)
            
        elif composition_type == "parallel":
            # Execute tools in parallel
            tasks = []
            for tool_spec in tools:
                task = self._execute_enhanced_tool(tool_spec, context)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "composition_type": "parallel",
                "tools": tools,
                "results": results,
                "successful": sum(1 for r in results if not isinstance(r, Exception))
            }
            
        elif composition_type == "conditional":
            # Execute tools based on conditions
            condition_results = []
            
            for tool_spec in tools:
                condition = tool_spec.get("condition", {})
                
                if self._evaluate_condition(condition, context):
                    result = await self._execute_enhanced_tool(tool_spec, context)
                    condition_results.append({
                        "tool": tool_spec["tool_name"],
                        "condition_met": True,
                        "result": result
                    })
                else:
                    condition_results.append({
                        "tool": tool_spec["tool_name"],
                        "condition_met": False,
                        "skipped": True
                    })
                    
            return {
                "composition_type": "conditional",
                "results": condition_results
            }
            
    async def _apply_validation_rule(self, rule: Dict[str, Any], data: Any) -> bool:
        """Apply a validation rule to data."""
        rule_type = rule.get("type")
        params = rule.get("params", {})
        
        if rule_type == "validate_expression":
            max_length = params.get("max_length", 100)
            if isinstance(data, dict) and "expression" in data:
                return len(str(data["expression"])) <= max_length
                
        elif rule_type == "validate_result":
            if isinstance(data, (int, float)):
                min_val = params.get("min", float('-inf'))
                max_val = params.get("max", float('inf'))
                return min_val <= data <= max_val
                
        elif rule_type == "validate_format":
            expected_format = params.get("format")
            # Add format validation logic
            return True
            
        return True
        
    def _is_cache_valid(self, cached_entry: Dict[str, Any], ttl: int) -> bool:
        """Check if cached entry is still valid."""
        if "timestamp" not in cached_entry:
            return False
            
        age = asyncio.get_event_loop().time() - cached_entry["timestamp"]
        return age < ttl
        
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a condition against context."""
        condition_type = condition.get("type", "equals")
        field = condition.get("field")
        value = condition.get("value")
        
        if not field:
            return True
            
        # Get field value from context
        field_value = context
        for part in field.split("."):
            if isinstance(field_value, dict):
                field_value = field_value.get(part)
            else:
                return False
                
        # Evaluate condition
        if condition_type == "equals":
            return field_value == value
        elif condition_type == "greater_than":
            return field_value > value
        elif condition_type == "less_than":
            return field_value < value
        elif condition_type == "contains":
            return value in str(field_value)
            
        return False
        
    async def discover_business_patterns(self) -> Dict[str, List[str]]:
        """Discover business logic patterns that can be applied to tools."""
        patterns = {
            "validation_patterns": [],
            "composition_patterns": [],
            "enhancement_patterns": []
        }
        
        # Analyze tool configurations for patterns
        for tool_name, config in self.tool_configs.items():
            # Check for validation opportunities
            if "parameters" in config:
                for param in config["parameters"]:
                    if param.get("type") in ["number", "integer"]:
                        patterns["validation_patterns"].append(
                            f"{tool_name}.{param['name']}: numeric_range_validation"
                        )
                    elif param.get("type") == "string" and param.get("pattern"):
                        patterns["validation_patterns"].append(
                            f"{tool_name}.{param['name']}: pattern_validation"
                        )
                        
            # Check for composition opportunities
            if "outputs" in config:
                for output in config["outputs"]:
                    matching_tools = self._find_tools_accepting_input(output["type"])
                    if matching_tools:
                        patterns["composition_patterns"].append(
                            f"{tool_name} -> {', '.join(matching_tools)}"
                        )
                        
        return patterns
        
    def _find_tools_accepting_input(self, input_type: str) -> List[str]:
        """Find tools that accept a specific input type."""
        matching_tools = []
        
        for tool_name, config in self.tool_configs.items():
            if "parameters" in config:
                for param in config["parameters"]:
                    if param.get("type") == input_type or param.get("accepts") == input_type:
                        matching_tools.append(tool_name)
                        break
                        
        return matching_tools
        
    async def optimize_tool_execution(self, tool_name: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize tool execution based on historical usage patterns."""
        optimizations = {
            "caching_recommendation": None,
            "parameter_defaults": {},
            "common_chains": [],
            "performance_hints": []
        }
        
        if not historical_data:
            return optimizations
            
        # Analyze parameter usage
        param_usage = {}
        for execution in historical_data:
            params = execution.get("parameters", {})
            for param, value in params.items():
                if param not in param_usage:
                    param_usage[param] = {}
                param_usage[param][str(value)] = param_usage[param].get(str(value), 0) + 1
                
        # Recommend defaults for commonly used values
        for param, usage in param_usage.items():
            most_common = max(usage.items(), key=lambda x: x[1])
            if most_common[1] > len(historical_data) * 0.6:  # Used >60% of time
                optimizations["parameter_defaults"][param] = most_common[0]
                
        # Analyze execution patterns
        execution_times = [e.get("execution_time", 0) for e in historical_data]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            
            if avg_time > 1.0:  # Slow execution
                optimizations["caching_recommendation"] = {
                    "enabled": True,
                    "ttl": 3600 if avg_time > 5.0 else 600
                }
                
        # Find common tool sequences
        # This would analyze logs to find tools commonly used together
        
        return optimizations
        
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check including Tool Kit specific metrics."""
        health_status = await super().health_check()
        
        # Add Tool Kit specific metrics
        health_status.update({
            "toolkit_path": str(self.toolkit_path),
            "discovered_tools": len(self.tool_configs),
            "tool_chains": list(self.tool_chains.keys()),
            "enhancements_loaded": len(self.business_enhancements),
            "cache_entries": len(self.tool_cache),
            "toolkit_integration": "active"
        })
        
        # Check Tool Kit availability
        if self.toolkit_path.exists():
            health_status["toolkit_accessible"] = True
        else:
            health_status["toolkit_accessible"] = False
            health_status["status"] = "degraded"
            
        return health_status