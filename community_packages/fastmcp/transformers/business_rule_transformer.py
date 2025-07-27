"""Business Rule Transformer for FastMCP.

This module provides transformers that inject business rule evaluation
into FastMCP tool execution.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from fastmcp import Tool, ToolError
import asyncio

@dataclass
class TransformationRule:
    """Rule for transforming tool behavior."""
    name: str
    description: str
    applies_to: Callable[[Tool, Dict[str, Any]], bool]
    transform: Callable[[Tool, Dict[str, Any]], Dict[str, Any]]
    priority: int = 0

class BusinessRuleTransformer:
    """Transformer that adds business rule evaluation to tools."""
    
    def __init__(self, orchestrator: Any):
        """Initialize with Business Logic Orchestrator."""
        self.orchestrator = orchestrator
        self.transformation_rules: List[TransformationRule] = []
        self.tool_mappings: Dict[str, str] = {}  # tool_name -> rule_set
    
    def transform_tool(self, tool: Tool) -> Tool:
        """Transform a tool to include business rule evaluation."""
        
        # Store original handler
        original_handler = tool.handler
        
        async def business_rule_handler(**kwargs) -> Any:
            """Enhanced handler with business rule evaluation."""
            
            # Get applicable rule set
            rule_set = self.tool_mappings.get(tool.name, "default")
            
            # Evaluate business rules
            rule_result = await self.orchestrator.evaluate_rule_set_async(
                rule_set=rule_set,
                context={
                    "tool_name": tool.name,
                    "tool_args": kwargs,
                    "tool_metadata": tool.metadata
                }
            )
            
            # Check if execution is allowed
            if not self._is_execution_allowed(rule_result):
                raise ToolError(
                    f"Tool execution blocked by business rules: "
                    f"{rule_result.get('denial_reason', 'Unknown')}"
                )
            
            # Apply any transformations
            transformed_kwargs = self._apply_transformations(
                tool,
                kwargs,
                rule_result
            )
            
            # Execute original handler with transformed arguments
            result = await original_handler(**transformed_kwargs)
            
            # Post-process result based on rules
            final_result = self._post_process_result(
                result,
                rule_result
            )
            
            # Audit the execution
            await self._audit_execution(
                tool=tool,
                args=kwargs,
                transformed_args=transformed_kwargs,
                result=final_result,
                rule_result=rule_result
            )
            
            return final_result
        
        # Create new tool with enhanced handler
        return Tool(
            name=tool.name,
            description=f"{tool.description} (Business Rule Enhanced)",
            handler=business_rule_handler,
            metadata={
                **tool.metadata,
                "business_rule_enhanced": True,
                "rule_set": self.tool_mappings.get(tool.name, "default")
            }
        )
    
    def register_transformation_rule(self, rule: TransformationRule) -> None:
        """Register a transformation rule."""
        self.transformation_rules.append(rule)
        self.transformation_rules.sort(key=lambda r: r.priority, reverse=True)
    
    def map_tool_to_rule_set(self, tool_name: str, rule_set: str) -> None:
        """Map a tool to a specific business rule set."""
        self.tool_mappings[tool_name] = rule_set
    
    def create_conditional_transformer(
        self,
        condition: Callable[[Dict[str, Any]], bool],
        transform_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> TransformationRule:
        """Create a conditional transformation rule."""
        
        def applies_to(tool: Tool, args: Dict[str, Any]) -> bool:
            return condition(args)
        
        def transform(tool: Tool, args: Dict[str, Any]) -> Dict[str, Any]:
            if condition(args):
                return transform_func(args)
            return args
        
        return TransformationRule(
            name="conditional_transform",
            description="Conditionally transform tool arguments",
            applies_to=applies_to,
            transform=transform,
            priority=5
        )
    
    def _is_execution_allowed(self, rule_result: Dict[str, Any]) -> bool:
        """Check if tool execution is allowed based on rules."""
        decision = rule_result.get("decision", "deny")
        return decision in ["allow", "allow_with_modifications"]
    
    def _apply_transformations(
        self,
        tool: Tool,
        args: Dict[str, Any],
        rule_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply transformations based on rules."""
        transformed = args.copy()
        
        # Apply rule-based modifications
        if rule_result.get("modifications"):
            transformed.update(rule_result["modifications"])
        
        # Apply transformation rules
        for rule in self.transformation_rules:
            if rule.applies_to(tool, transformed):
                transformed = rule.transform(tool, transformed)
        
        return transformed
    
    def _post_process_result(
        self,
        result: Any,
        rule_result: Dict[str, Any]
    ) -> Any:
        """Post-process result based on business rules."""
        
        # Apply any result filters
        if rule_result.get("result_filters"):
            for filter_func in rule_result["result_filters"]:
                result = filter_func(result)
        
        # Apply data masking if required
        if rule_result.get("mask_fields") and isinstance(result, dict):
            for field in rule_result["mask_fields"]:
                if field in result:
                    result[field] = "[REDACTED]"
        
        return result
    
    async def _audit_execution(
        self,
        tool: Tool,
        args: Dict[str, Any],
        transformed_args: Dict[str, Any],
        result: Any,
        rule_result: Dict[str, Any]
    ) -> None:
        """Audit tool execution for compliance."""
        audit_entry = {
            "tool_name": tool.name,
            "original_args": args,
            "transformed_args": transformed_args,
            "transformations_applied": transformed_args != args,
            "rule_decision": rule_result.get("decision"),
            "applied_rules": rule_result.get("applied_rules", []),
            "execution_time": asyncio.get_event_loop().time()
        }
        
        # Send to orchestrator for logging
        await self.orchestrator.log_audit_entry(audit_entry)

# Example transformation patterns
def create_rate_limit_transformer(
    max_calls_per_minute: int
) -> TransformationRule:
    """Create a rate limiting transformation."""
    call_times: List[float] = []
    
    def applies_to(tool: Tool, args: Dict[str, Any]) -> bool:
        current_time = asyncio.get_event_loop().time()
        
        # Clean old entries
        nonlocal call_times
        call_times = [t for t in call_times if current_time - t < 60]
        
        return len(call_times) >= max_calls_per_minute
    
    def transform(tool: Tool, args: Dict[str, Any]) -> Dict[str, Any]:
        raise ToolError(f"Rate limit exceeded: {max_calls_per_minute} calls per minute")
    
    return TransformationRule(
        name="rate_limiter",
        description=f"Limit tool calls to {max_calls_per_minute} per minute",
        applies_to=applies_to,
        transform=transform,
        priority=100  # High priority to execute first
    )