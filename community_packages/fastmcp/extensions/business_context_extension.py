"""Business Context Extension for FastMCP.

This module extends FastMCP with business context metadata support,
enabling tools to understand and respect business rules.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from fastmcp import FastMCP, Context

@dataclass
class BusinessContext:
    """Business context for tool execution."""
    user_role: str
    department: str
    clearance_level: int
    active_rules: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BusinessRule:
    """Business rule definition for tools."""
    name: str
    description: str
    condition: Callable[[BusinessContext, Dict[str, Any]], bool]
    action: str  # allow, deny, modify
    modifications: Optional[Dict[str, Any]] = None
    priority: int = 0

class BusinessContextExtension:
    """FastMCP extension for business context awareness."""
    
    def __init__(self, orchestrator: Optional[Any] = None):
        """Initialize with optional orchestrator connection."""
        self.orchestrator = orchestrator
        self.rules: Dict[str, List[BusinessRule]] = {}
        self.context_validators: List[Callable] = []
        self.audit_logger: Optional[Callable] = None
    
    def apply_to_server(self, server: FastMCP) -> None:
        """Apply business context extension to FastMCP server."""
        
        # Add business context to server state
        server.state["business_context"] = None
        server.state["business_rules"] = self.rules
        
        # Wrap tool execution with business logic
        original_call_tool = server.call_tool
        
        async def business_aware_call_tool(
            name: str,
            arguments: Dict[str, Any],
            context: Context
        ) -> Any:
            """Enhanced tool execution with business context."""
            
            # Extract business context
            business_context = self._extract_business_context(context)
            
            # Validate context
            if not self._validate_context(business_context):
                raise ValueError("Invalid business context")
            
            # Apply business rules
            tool_rules = self.rules.get(name, [])
            final_arguments = arguments.copy()
            
            for rule in sorted(tool_rules, key=lambda r: r.priority, reverse=True):
                if rule.condition(business_context, arguments):
                    if rule.action == "deny":
                        self._audit_log(
                            "tool_denied",
                            tool=name,
                            rule=rule.name,
                            context=business_context
                        )
                        raise PermissionError(
                            f"Tool execution denied by rule: {rule.name}"
                        )
                    
                    elif rule.action == "modify" and rule.modifications:
                        final_arguments.update(rule.modifications)
                        self._audit_log(
                            "tool_modified",
                            tool=name,
                            rule=rule.name,
                            modifications=rule.modifications,
                            context=business_context
                        )
            
            # Execute tool with final arguments
            result = await original_call_tool(name, final_arguments, context)
            
            # Audit successful execution
            self._audit_log(
                "tool_executed",
                tool=name,
                arguments=final_arguments,
                context=business_context
            )
            
            return result
        
        server.call_tool = business_aware_call_tool
    
    def register_rule(self, tool_name: str, rule: BusinessRule) -> None:
        """Register a business rule for a specific tool."""
        if tool_name not in self.rules:
            self.rules[tool_name] = []
        
        self.rules[tool_name].append(rule)
    
    def register_context_validator(self, validator: Callable) -> None:
        """Register a context validator function."""
        self.context_validators.append(validator)
    
    def set_audit_logger(self, logger: Callable) -> None:
        """Set audit logging function."""
        self.audit_logger = logger
    
    def create_tool_decorator(self) -> Callable:
        """Create decorator for business-aware tools."""
        
        def business_context_required(
            required_clearance: int = 0,
            required_departments: Optional[List[str]] = None
        ):
            """Decorator to enforce business context requirements."""
            
            def decorator(func: Callable) -> Callable:
                async def wrapper(
                    *args,
                    business_context: Optional[BusinessContext] = None,
                    **kwargs
                ):
                    # Validate business context
                    if not business_context:
                        raise ValueError("Business context required")
                    
                    # Check clearance level
                    if business_context.clearance_level < required_clearance:
                        raise PermissionError(
                            f"Insufficient clearance level. "
                            f"Required: {required_clearance}, "
                            f"Current: {business_context.clearance_level}"
                        )
                    
                    # Check department
                    if required_departments and \
                       business_context.department not in required_departments:
                        raise PermissionError(
                            f"Access restricted to departments: {required_departments}"
                        )
                    
                    # Execute original function
                    return await func(*args, **kwargs)
                
                return wrapper
            return decorator
        
        return business_context_required
    
    def _extract_business_context(self, context: Context) -> BusinessContext:
        """Extract business context from FastMCP context."""
        # Look for business context in various places
        if hasattr(context, 'business_context'):
            return context.business_context
        
        # Try to construct from available data
        return BusinessContext(
            user_role=context.get('user_role', 'user'),
            department=context.get('department', 'general'),
            clearance_level=context.get('clearance_level', 0),
            active_rules=context.get('active_rules', []),
            constraints=context.get('constraints', {}),
            metadata=context.get('metadata', {})
        )
    
    def _validate_context(self, context: BusinessContext) -> bool:
        """Validate business context using registered validators."""
        for validator in self.context_validators:
            if not validator(context):
                return False
        return True
    
    def _audit_log(self, event_type: str, **kwargs) -> None:
        """Log audit events."""
        if self.audit_logger:
            self.audit_logger(event_type, **kwargs)

# Example usage patterns
def create_department_rule(
    department: str,
    allowed_tools: List[str]
) -> BusinessRule:
    """Create a rule that restricts tools to specific departments."""
    
    def condition(context: BusinessContext, args: Dict[str, Any]) -> bool:
        return context.department != department
    
    return BusinessRule(
        name=f"department_{department}_restriction",
        description=f"Restrict tools to {department} department",
        condition=condition,
        action="deny",
        priority=10
    )

def create_data_limit_rule(
    max_records: int
) -> BusinessRule:
    """Create a rule that limits data access."""
    
    def condition(context: BusinessContext, args: Dict[str, Any]) -> bool:
        return args.get('limit', 0) > max_records
    
    return BusinessRule(
        name="data_limit_rule",
        description=f"Limit data access to {max_records} records",
        condition=condition,
        action="modify",
        modifications={"limit": max_records},
        priority=5
    )