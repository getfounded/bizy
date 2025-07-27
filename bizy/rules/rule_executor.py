"""
Rule Executor: Executes parsed and validated business rules.

This module provides the execution engine for business rules, handling
condition evaluation, action execution, and error recovery.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction
from ..core.meta_orchestrator import MetaOrchestrator
from ..events import EventBus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for rule execution."""
    rule_id: str
    start_time: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional['ExecutionContext'] = None
    
    def get_value(self, field: str) -> Any:
        """Get value from context, supporting nested fields."""
        # Support dot notation for nested fields
        parts = field.split('.')
        value = self.data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
                
        return value
        
    def set_value(self, field: str, value: Any):
        """Set value in context, supporting nested fields."""
        parts = field.split('.')
        target = self.data
        
        # Navigate to parent of target field
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
            
        # Set the value
        target[parts[-1]] = value
        
    def create_child(self, rule_id: str) -> 'ExecutionContext':
        """Create child context for sub-rule execution."""
        return ExecutionContext(
            rule_id=rule_id,
            start_time=datetime.utcnow(),
            data=self.data.copy(),
            metadata=self.metadata.copy(),
            parent_context=self
        )


@dataclass
class ExecutionResult:
    """Result of rule execution."""
    rule_id: str
    success: bool
    start_time: datetime
    end_time: datetime
    conditions_evaluated: List[Tuple[RuleCondition, bool]]
    actions_executed: List[Tuple[RuleAction, Any]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


class RuleExecutor:
    """
    Executes business rules with comprehensive error handling.
    
    Features:
    - Condition evaluation with short-circuit logic
    - Parallel and sequential action execution
    - Error recovery and retry logic
    - Execution tracing and monitoring
    - Sub-rule and workflow support
    """
    
    def __init__(
        self,
        orchestrator: MetaOrchestrator,
        event_bus: Optional[EventBus] = None
    ):
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.execution_cache: Dict[str, ExecutionResult] = {}
        self.running_rules: Set[str] = set()
        
    async def execute(
        self,
        rule: BusinessRule,
        context: Union[Dict[str, Any], ExecutionContext],
        trace: bool = True
    ) -> ExecutionResult:
        """
        Execute a business rule.
        
        Args:
            rule: BusinessRule to execute
            context: Execution context (dict or ExecutionContext)
            trace: Whether to enable execution tracing
            
        Returns:
            ExecutionResult with execution details
        """
        # Convert dict to ExecutionContext if needed
        if isinstance(context, dict):
            context = ExecutionContext(
                rule_id=rule.id,
                start_time=datetime.utcnow(),
                data=context
            )
            
        # Check if rule is already running (prevent recursion)
        if rule.id in self.running_rules:
            logger.warning(f"Rule {rule.id} is already executing, skipping to prevent recursion")
            return ExecutionResult(
                rule_id=rule.id,
                success=False,
                start_time=context.start_time,
                end_time=datetime.utcnow(),
                conditions_evaluated=[],
                actions_executed=[],
                errors=[f"Rule {rule.id} is already executing"],
                warnings=[]
            )
            
        # Mark rule as running
        self.running_rules.add(rule.id)
        
        try:
            # Execute the rule
            result = await self._execute_rule(rule, context, trace)
            
            # Cache result
            self.execution_cache[rule.id] = result
            
            # Publish execution event
            if self.event_bus:
                await self.event_bus.publish(
                    "rule_executed",
                    {
                        "rule_id": rule.id,
                        "success": result.success,
                        "duration": result.duration,
                        "errors": result.errors
                    }
                )
                
            return result
            
        finally:
            # Remove from running rules
            self.running_rules.discard(rule.id)
            
    async def _execute_rule(
        self,
        rule: BusinessRule,
        context: ExecutionContext,
        trace: bool
    ) -> ExecutionResult:
        """Internal rule execution logic."""
        start_time = datetime.utcnow()
        conditions_evaluated = []
        actions_executed = []
        errors = []
        warnings = []
        
        # Check if rule is enabled
        if not rule.enabled:
            return ExecutionResult(
                rule_id=rule.id,
                success=False,
                start_time=start_time,
                end_time=datetime.utcnow(),
                conditions_evaluated=[],
                actions_executed=[],
                errors=["Rule is disabled"],
                warnings=[]
            )
            
        try:
            # Evaluate conditions
            conditions_passed, conditions_evaluated = await self._evaluate_conditions(
                rule.conditions, context
            )
            
            if not conditions_passed:
                # Conditions not met
                return ExecutionResult(
                    rule_id=rule.id,
                    success=True,  # Not an error, just conditions not met
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    conditions_evaluated=conditions_evaluated,
                    actions_executed=[],
                    errors=[],
                    warnings=["Conditions not met"]
                )
                
            # Execute actions
            action_results, action_errors = await self._execute_actions(
                rule.actions, context, rule.retry_count
            )
            
            actions_executed = action_results
            errors.extend(action_errors)
            
            # Handle fallback rule if there were errors
            if errors and rule.fallback_rule:
                logger.info(f"Executing fallback rule: {rule.fallback_rule}")
                # TODO: Load and execute fallback rule
                warnings.append(f"Fallback rule {rule.fallback_rule} would be executed")
                
            # Determine success
            success = len(errors) == 0
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.id}: {e}")
            errors.append(str(e))
            success = False
            
        return ExecutionResult(
            rule_id=rule.id,
            success=success,
            start_time=start_time,
            end_time=datetime.utcnow(),
            conditions_evaluated=conditions_evaluated,
            actions_executed=actions_executed,
            errors=errors,
            warnings=warnings,
            metadata={
                "trace_enabled": trace,
                "context_data_keys": list(context.data.keys())
            }
        )
        
    async def _evaluate_conditions(
        self,
        conditions: List[RuleCondition],
        context: ExecutionContext
    ) -> Tuple[bool, List[Tuple[RuleCondition, bool]]]:
        """Evaluate rule conditions."""
        if not conditions:
            return True, []
            
        evaluated = []
        
        # Group conditions by combinator
        groups = {}
        for condition in conditions:
            combinator = condition.combinator or "all"
            if combinator not in groups:
                groups[combinator] = []
            groups[combinator].append(condition)
            
        # Evaluate each group
        group_results = {}
        
        for combinator, group_conditions in groups.items():
            if combinator == "all":
                # All conditions must be true
                group_result = True
                for condition in group_conditions:
                    result = await self._evaluate_condition(condition, context)
                    evaluated.append((condition, result))
                    if not result:
                        group_result = False
                        # Short-circuit for "all"
                        if not condition.continue_on_error:
                            break
                group_results[combinator] = group_result
                
            elif combinator == "any":
                # Any condition must be true
                group_result = False
                for condition in group_conditions:
                    result = await self._evaluate_condition(condition, context)
                    evaluated.append((condition, result))
                    if result:
                        group_result = True
                        # Short-circuit for "any"
                        if not condition.continue_on_error:
                            break
                group_results[combinator] = group_result
                
            elif combinator == "not":
                # All conditions must be false
                group_result = True
                for condition in group_conditions:
                    result = await self._evaluate_condition(condition, context)
                    evaluated.append((condition, result))
                    if result:
                        group_result = False
                        # Short-circuit for "not"
                        if not condition.continue_on_error:
                            break
                group_results[combinator] = group_result
                
        # Combine group results (default to AND between groups)
        overall_result = all(group_results.values()) if group_results else True
        
        return overall_result, evaluated
        
    async def _evaluate_condition(
        self,
        condition: RuleCondition,
        context: ExecutionContext
    ) -> bool:
        """Evaluate a single condition."""
        try:
            # Get field value from context
            field_value = context.get_value(condition.field)
            
            # Handle null values
            if field_value is None:
                return condition.operator in ["not_equals", "not_contains", "not_in"]
                
            # Evaluate based on operator
            result = self._apply_operator(
                field_value,
                condition.operator,
                condition.value,
                condition.case_sensitive
            )
            
            logger.debug(f"Condition {condition.field} {condition.operator} {condition.value} = {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.field}: {e}")
            return False
            
    def _apply_operator(
        self,
        field_value: Any,
        operator: str,
        condition_value: Any,
        case_sensitive: bool = True
    ) -> bool:
        """Apply comparison operator."""
        try:
            # String normalization for case-insensitive comparison
            if not case_sensitive and isinstance(field_value, str) and isinstance(condition_value, str):
                field_value = field_value.lower()
                condition_value = condition_value.lower()
                
            # Apply operator
            if operator == "equals":
                return field_value == condition_value
            elif operator == "not_equals":
                return field_value != condition_value
            elif operator == "greater_than":
                return field_value > condition_value
            elif operator == "less_than":
                return field_value < condition_value
            elif operator == "greater_or_equal":
                return field_value >= condition_value
            elif operator == "less_or_equal":
                return field_value <= condition_value
            elif operator == "contains":
                return condition_value in str(field_value)
            elif operator == "not_contains":
                return condition_value not in str(field_value)
            elif operator == "starts_with":
                return str(field_value).startswith(str(condition_value))
            elif operator == "ends_with":
                return str(field_value).endswith(str(condition_value))
            elif operator == "regex":
                return bool(re.match(str(condition_value), str(field_value)))
            elif operator == "in":
                return field_value in condition_value
            elif operator == "not_in":
                return field_value not in condition_value
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying operator {operator}: {e}")
            return False
            
    async def _execute_actions(
        self,
        actions: List[RuleAction],
        context: ExecutionContext,
        retry_count: int = 0
    ) -> Tuple[List[Tuple[RuleAction, Any]], List[str]]:
        """Execute rule actions."""
        results = []
        errors = []
        
        # Group actions by parallelism
        parallel_groups = self._group_parallel_actions(actions)
        
        for group in parallel_groups:
            if len(group) == 1:
                # Single action, execute directly
                action = group[0]
                result, error = await self._execute_single_action(
                    action, context, retry_count
                )
                
                if result is not None:
                    results.append((action, result))
                if error:
                    errors.append(error)
                    if not action.continue_on_error:
                        break  # Stop execution on error
                        
            else:
                # Multiple actions, execute in parallel
                tasks = [
                    self._execute_single_action(action, context, retry_count)
                    for action in group
                ]
                
                group_results = await asyncio.gather(*tasks)
                
                for action, (result, error) in zip(group, group_results):
                    if result is not None:
                        results.append((action, result))
                    if error:
                        errors.append(error)
                        
                # Check if any action requires stopping on error
                if any(
                    error and not action.continue_on_error
                    for action, (_, error) in zip(group, group_results)
                ):
                    break  # Stop execution
                    
        return results, errors
        
    async def _execute_single_action(
        self,
        action: RuleAction,
        context: ExecutionContext,
        retry_count: int = 0
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Execute a single action with retry logic."""
        max_retries = action.retry_count if action.retry_count is not None else retry_count
        
        for attempt in range(max_retries + 1):
            try:
                # Execute via orchestrator
                result = await self.orchestrator.execute_action(
                    action.framework,
                    action.action,
                    {
                        **action.parameters,
                        "_context": context.data,
                        "_metadata": context.metadata
                    }
                )
                
                # Update context with result
                if isinstance(result, dict) and "_output" in result:
                    context.set_value(f"_action_results.{action.action}", result["_output"])
                    
                return result, None
                
            except Exception as e:
                error_msg = f"Error executing action {action.action} on {action.framework}: {e}"
                logger.error(error_msg)
                
                if attempt < max_retries:
                    logger.info(f"Retrying action {action.action} (attempt {attempt + 2}/{max_retries + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None, error_msg
                    
        return None, f"Action {action.action} failed after {max_retries + 1} attempts"
        
    def _group_parallel_actions(self, actions: List[RuleAction]) -> List[List[RuleAction]]:
        """Group actions for parallel execution."""
        groups = []
        current_group = []
        
        for action in actions:
            if action.depends_on:
                # Action has dependencies, start new group
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([action])
            else:
                # No dependencies, can be parallelized
                current_group.append(action)
                
        if current_group:
            groups.append(current_group)
            
        return groups
        
    async def execute_batch(
        self,
        rules: List[BusinessRule],
        context: Union[Dict[str, Any], ExecutionContext],
        parallel: bool = True
    ) -> List[ExecutionResult]:
        """
        Execute multiple rules.
        
        Args:
            rules: List of rules to execute
            context: Execution context
            parallel: Whether to execute rules in parallel
            
        Returns:
            List of execution results
        """
        if parallel:
            # Execute rules in parallel
            tasks = [
                self.execute(rule, context)
                for rule in rules
            ]
            results = await asyncio.gather(*tasks)
        else:
            # Execute rules sequentially
            results = []
            for rule in rules:
                result = await self.execute(rule, context)
                results.append(result)
                
        return results
        
    def get_execution_trace(self, rule_id: str) -> Optional[ExecutionResult]:
        """Get execution trace for a rule."""
        return self.execution_cache.get(rule_id)
        
    def clear_execution_cache(self):
        """Clear execution cache."""
        self.execution_cache.clear()
        
    async def validate_execution_permissions(
        self,
        rule: BusinessRule,
        user_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if user has permissions to execute rule.
        
        Args:
            rule: Rule to validate
            user_context: User context with roles/permissions
            
        Returns:
            Tuple of (allowed, reasons)
        """
        allowed = True
        reasons = []
        
        # Check rule-level permissions
        if "required_roles" in rule.metadata:
            user_roles = set(user_context.get("roles", []))
            required_roles = set(rule.metadata["required_roles"])
            
            if not required_roles.intersection(user_roles):
                allowed = False
                reasons.append(f"User lacks required roles: {required_roles}")
                
        # Check action-level permissions
        for action in rule.actions:
            if "required_permission" in action.parameters:
                permission = action.parameters["required_permission"]
                user_permissions = user_context.get("permissions", [])
                
                if permission not in user_permissions:
                    allowed = False
                    reasons.append(f"User lacks permission for action {action.action}: {permission}")
                    
        return allowed, reasons