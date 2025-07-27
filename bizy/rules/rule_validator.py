"""
Rule Validator: Validates business rule definitions.

This module provides comprehensive validation for business rules including
syntax, semantics, framework compatibility, and execution safety.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import re
import logging
from dataclasses import dataclass

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction
from ..core.meta_orchestrator import MetaOrchestrator
from ..core.framework_adapter import FrameworkCapability

logger = logging.getLogger(__name__)


class RuleValidationError(Exception):
    """Raised when rule validation fails."""
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or []
        super().__init__(message)


@dataclass
class ValidationResult:
    """Result of rule validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.valid


class RuleValidator:
    """
    Validates business rule definitions for correctness and safety.
    
    Validation includes:
    - Syntax validation
    - Semantic validation
    - Framework compatibility
    - Security checks
    - Performance analysis
    - Conflict detection
    """
    
    def __init__(self, orchestrator: Optional[MetaOrchestrator] = None):
        self.orchestrator = orchestrator
        self.field_validators: Dict[str, Callable] = {}
        self.operator_validators: Dict[str, Callable] = {}
        self._initialize_validators()
        
    def _initialize_validators(self):
        """Initialize built-in validators."""
        # Field validators
        self.field_validators = {
            "email": self._validate_email_field,
            "url": self._validate_url_field,
            "date": self._validate_date_field,
            "number": self._validate_number_field,
            "regex": self._validate_regex_field
        }
        
        # Operator validators
        self.operator_validators = {
            "regex": self._validate_regex_operator,
            "in": self._validate_in_operator,
            "not_in": self._validate_in_operator
        }
        
    def validate(self, rule: BusinessRule) -> ValidationResult:
        """
        Perform comprehensive validation of a business rule.
        
        Args:
            rule: BusinessRule to validate
            
        Returns:
            ValidationResult with errors, warnings, and suggestions
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        basic_errors = self._validate_basic_fields(rule)
        errors.extend(basic_errors)
        
        # Validate conditions
        cond_errors, cond_warnings = self._validate_conditions(rule.conditions)
        errors.extend(cond_errors)
        warnings.extend(cond_warnings)
        
        # Validate actions
        act_errors, act_warnings, act_suggestions = self._validate_actions(rule.actions)
        errors.extend(act_errors)
        warnings.extend(act_warnings)
        suggestions.extend(act_suggestions)
        
        # Validate framework compatibility
        if self.orchestrator:
            compat_errors = self._validate_framework_compatibility(rule)
            errors.extend(compat_errors)
            
        # Validate security
        sec_errors, sec_warnings = self._validate_security(rule)
        errors.extend(sec_errors)
        warnings.extend(sec_warnings)
        
        # Validate performance
        perf_warnings, perf_suggestions = self._validate_performance(rule)
        warnings.extend(perf_warnings)
        suggestions.extend(perf_suggestions)
        
        # Check for conflicts
        conflict_warnings = self._check_conflicts(rule)
        warnings.extend(conflict_warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def _validate_basic_fields(self, rule: BusinessRule) -> List[str]:
        """Validate basic rule fields."""
        errors = []
        
        # Validate ID
        if not rule.id:
            errors.append("Rule ID is required")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', rule.id):
            errors.append("Rule ID must contain only alphanumeric characters, underscores, and hyphens")
            
        # Validate name
        if not rule.name:
            errors.append("Rule name is required")
        elif len(rule.name) > 100:
            errors.append("Rule name must be 100 characters or less")
            
        # Validate priority
        valid_priorities = {"low", "medium", "high", "critical"}
        if rule.priority not in valid_priorities:
            errors.append(f"Invalid priority '{rule.priority}'. Must be one of: {', '.join(valid_priorities)}")
            
        # Validate actions exist
        if not rule.actions:
            errors.append("Rule must have at least one action")
            
        return errors
        
    def _validate_conditions(self, conditions: List[RuleCondition]) -> Tuple[List[str], List[str]]:
        """Validate rule conditions."""
        errors = []
        warnings = []
        
        for i, condition in enumerate(conditions):
            # Validate field
            if not condition.field:
                errors.append(f"Condition {i+1}: Field is required")
                
            # Validate operator
            valid_operators = {
                "equals", "not_equals", "greater_than", "less_than",
                "greater_or_equal", "less_or_equal", "contains", "not_contains",
                "starts_with", "ends_with", "regex", "in", "not_in"
            }
            
            if condition.operator not in valid_operators:
                errors.append(f"Condition {i+1}: Invalid operator '{condition.operator}'")
                
            # Validate value
            if condition.value is None:
                errors.append(f"Condition {i+1}: Value is required")
            else:
                # Operator-specific validation
                if condition.operator in self.operator_validators:
                    op_errors = self.operator_validators[condition.operator](condition)
                    errors.extend(op_errors)
                    
            # Check for field-specific validation
            field_type = self._infer_field_type(condition.field)
            if field_type in self.field_validators:
                field_errors = self.field_validators[field_type](condition)
                errors.extend(field_errors)
                
            # Validate combinator
            valid_combinators = {"all", "any", "not"}
            if condition.combinator and condition.combinator not in valid_combinators:
                errors.append(f"Condition {i+1}: Invalid combinator '{condition.combinator}'")
                
        # Check for redundant conditions
        redundant = self._find_redundant_conditions(conditions)
        for cond1, cond2 in redundant:
            warnings.append(f"Redundant conditions detected: '{cond1.field} {cond1.operator} {cond1.value}' and '{cond2.field} {cond2.operator} {cond2.value}'")
            
        # Check for contradictory conditions
        contradictions = self._find_contradictory_conditions(conditions)
        for cond1, cond2 in contradictions:
            errors.append(f"Contradictory conditions: '{cond1.field} {cond1.operator} {cond1.value}' and '{cond2.field} {cond2.operator} {cond2.value}'")
            
        return errors, warnings
        
    def _validate_actions(self, actions: List[RuleAction]) -> Tuple[List[str], List[str], List[str]]:
        """Validate rule actions."""
        errors = []
        warnings = []
        suggestions = []
        
        # Track frameworks used
        frameworks_used = set()
        
        for i, action in enumerate(actions):
            # Validate framework
            if not action.framework:
                errors.append(f"Action {i+1}: Framework is required")
            else:
                frameworks_used.add(action.framework)
                
            # Validate action name
            if not action.action:
                errors.append(f"Action {i+1}: Action name is required")
                
            # Validate parameters
            if action.parameters:
                param_errors = self._validate_action_parameters(action)
                errors.extend(param_errors)
                
            # Validate timeout
            if action.timeout is not None:
                if not isinstance(action.timeout, (int, float)):
                    errors.append(f"Action {i+1}: Timeout must be a number")
                elif action.timeout <= 0:
                    errors.append(f"Action {i+1}: Timeout must be positive")
                elif action.timeout > 300:
                    warnings.append(f"Action {i+1}: Timeout of {action.timeout}s is very long")
                    
            # Validate retry count
            if action.retry_count is not None:
                if not isinstance(action.retry_count, int):
                    errors.append(f"Action {i+1}: Retry count must be an integer")
                elif action.retry_count < 0:
                    errors.append(f"Action {i+1}: Retry count must be non-negative")
                elif action.retry_count > 10:
                    warnings.append(f"Action {i+1}: Retry count of {action.retry_count} is very high")
                    
        # Check for framework diversity
        if len(frameworks_used) == 1:
            suggestions.append("Consider using multiple frameworks to leverage cross-framework coordination benefits")
            
        # Check for action dependencies
        dep_warnings = self._check_action_dependencies(actions)
        warnings.extend(dep_warnings)
        
        return errors, warnings, suggestions
        
    def _validate_framework_compatibility(self, rule: BusinessRule) -> List[str]:
        """Validate framework compatibility."""
        errors = []
        
        if not self.orchestrator:
            return errors
            
        # Check each action's framework
        for i, action in enumerate(rule.actions):
            # Check if framework adapter exists
            if action.framework not in self.orchestrator.adapters:
                errors.append(f"Action {i+1}: Framework '{action.framework}' not available")
                continue
                
            # Check if adapter is connected
            adapter = self.orchestrator.adapters[action.framework]
            if not adapter.is_connected:
                errors.append(f"Action {i+1}: Framework '{action.framework}' is not connected")
                
            # Check if action is supported
            capabilities = adapter.get_capabilities()
            if not self._is_action_supported(action.action, capabilities):
                errors.append(f"Action {i+1}: Action '{action.action}' not supported by framework '{action.framework}'")
                
        return errors
        
    def _validate_security(self, rule: BusinessRule) -> Tuple[List[str], List[str]]:
        """Validate security aspects of the rule."""
        errors = []
        warnings = []
        
        # Check for sensitive data in conditions
        sensitive_fields = {"password", "token", "secret", "key", "credential"}
        for condition in rule.conditions:
            if any(sensitive in condition.field.lower() for sensitive in sensitive_fields):
                warnings.append(f"Condition on potentially sensitive field '{condition.field}'")
                
        # Check for dangerous actions
        dangerous_actions = {"execute_code", "run_command", "system_call", "eval"}
        for i, action in enumerate(rule.actions):
            if any(dangerous in action.action.lower() for dangerous in dangerous_actions):
                errors.append(f"Action {i+1}: Potentially dangerous action '{action.action}'")
                
        # Check for injection vulnerabilities
        for i, action in enumerate(rule.actions):
            if action.parameters:
                injection_risks = self._check_injection_risks(action.parameters)
                for risk in injection_risks:
                    warnings.append(f"Action {i+1}: Potential injection risk in parameter '{risk}'")
                    
        return errors, warnings
        
    def _validate_performance(self, rule: BusinessRule) -> Tuple[List[str], List[str]]:
        """Validate performance aspects of the rule."""
        warnings = []
        suggestions = []
        
        # Check action count
        if len(rule.actions) > 10:
            warnings.append(f"Rule has {len(rule.actions)} actions, which may impact performance")
            
        # Check condition complexity
        if len(rule.conditions) > 20:
            warnings.append(f"Rule has {len(rule.conditions)} conditions, consider simplifying")
            
        # Check for expensive operations
        expensive_operations = {"ml_inference", "large_data_processing", "complex_query"}
        expensive_count = sum(
            1 for action in rule.actions
            if any(op in action.action.lower() for op in expensive_operations)
        )
        
        if expensive_count > 3:
            warnings.append(f"Rule contains {expensive_count} potentially expensive operations")
            suggestions.append("Consider caching results or optimizing expensive operations")
            
        # Check for sequential dependencies
        if self._has_sequential_dependencies(rule.actions):
            suggestions.append("Consider parallelizing independent actions for better performance")
            
        return warnings, suggestions
        
    def _check_conflicts(self, rule: BusinessRule) -> List[str]:
        """Check for potential conflicts in the rule."""
        warnings = []
        
        # Check for action conflicts
        action_pairs = [
            ("create", "delete"),
            ("enable", "disable"),
            ("start", "stop"),
            ("approve", "reject")
        ]
        
        for action1, action2 in action_pairs:
            has_action1 = any(action1 in a.action.lower() for a in rule.actions)
            has_action2 = any(action2 in a.action.lower() for a in rule.actions)
            
            if has_action1 and has_action2:
                warnings.append(f"Rule contains potentially conflicting actions: '{action1}' and '{action2}'")
                
        return warnings
        
    # Helper methods
    
    def _infer_field_type(self, field: str) -> Optional[str]:
        """Infer field type from field name."""
        if "email" in field.lower():
            return "email"
        elif "url" in field.lower() or "link" in field.lower():
            return "url"
        elif "date" in field.lower() or "time" in field.lower():
            return "date"
        elif any(num in field.lower() for num in ["amount", "count", "quantity", "price", "score"]):
            return "number"
        return None
        
    def _validate_email_field(self, condition: RuleCondition) -> List[str]:
        """Validate email field conditions."""
        errors = []
        
        if condition.operator in ["equals", "not_equals", "contains"] and isinstance(condition.value, str):
            # Basic email format check
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if condition.operator == "equals" and not re.match(email_pattern, condition.value):
                errors.append(f"Invalid email format in condition: {condition.value}")
                
        return errors
        
    def _validate_url_field(self, condition: RuleCondition) -> List[str]:
        """Validate URL field conditions."""
        errors = []
        
        if condition.operator in ["equals", "not_equals", "starts_with"] and isinstance(condition.value, str):
            # Basic URL format check
            url_pattern = r'^https?://'
            if condition.operator == "equals" and not re.match(url_pattern, condition.value):
                errors.append(f"Invalid URL format in condition: {condition.value}")
                
        return errors
        
    def _validate_date_field(self, condition: RuleCondition) -> List[str]:
        """Validate date field conditions."""
        errors = []
        
        if condition.operator in ["greater_than", "less_than", "equals"] and isinstance(condition.value, str):
            # Check for common date formats
            date_patterns = [
                r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
                r'^\d{2}-\d{2}-\d{4}$'   # DD-MM-YYYY
            ]
            
            if not any(re.match(pattern, condition.value) for pattern in date_patterns):
                errors.append(f"Unrecognized date format in condition: {condition.value}")
                
        return errors
        
    def _validate_number_field(self, condition: RuleCondition) -> List[str]:
        """Validate number field conditions."""
        errors = []
        
        if condition.operator in ["greater_than", "less_than", "equals", "greater_or_equal", "less_or_equal"]:
            if not isinstance(condition.value, (int, float)):
                try:
                    float(condition.value)
                except (ValueError, TypeError):
                    errors.append(f"Expected numeric value for condition, got: {condition.value}")
                    
        return errors
        
    def _validate_regex_field(self, condition: RuleCondition) -> List[str]:
        """Validate regex field conditions."""
        return self._validate_regex_operator(condition) if condition.operator == "regex" else []
        
    def _validate_regex_operator(self, condition: RuleCondition) -> List[str]:
        """Validate regex operator usage."""
        errors = []
        
        if isinstance(condition.value, str):
            try:
                re.compile(condition.value)
            except re.error as e:
                errors.append(f"Invalid regex pattern in condition: {e}")
                
        else:
            errors.append(f"Regex operator requires string value, got: {type(condition.value).__name__}")
            
        return errors
        
    def _validate_in_operator(self, condition: RuleCondition) -> List[str]:
        """Validate in/not_in operator usage."""
        errors = []
        
        if not isinstance(condition.value, list):
            errors.append(f"Operator '{condition.operator}' requires list value, got: {type(condition.value).__name__}")
        elif len(condition.value) == 0:
            errors.append(f"Operator '{condition.operator}' requires non-empty list")
            
        return errors
        
    def _validate_action_parameters(self, action: RuleAction) -> List[str]:
        """Validate action parameters."""
        errors = []
        
        # Check for required parameters based on action type
        required_params = self._get_required_parameters(action.framework, action.action)
        
        for param in required_params:
            if param not in action.parameters:
                errors.append(f"Action '{action.action}' missing required parameter '{param}'")
                
        # Validate parameter types
        param_types = self._get_parameter_types(action.framework, action.action)
        
        for param, expected_type in param_types.items():
            if param in action.parameters:
                value = action.parameters[param]
                if not isinstance(value, expected_type):
                    errors.append(f"Parameter '{param}' expected type {expected_type.__name__}, got {type(value).__name__}")
                    
        return errors
        
    def _get_required_parameters(self, framework: str, action: str) -> List[str]:
        """Get required parameters for an action."""
        # This would be populated from framework metadata
        required_params_map = {
            ("langchain", "analyze_sentiment"): ["text"],
            ("temporal", "start_workflow"): ["workflow_name"],
            ("mcp", "execute_tool"): ["tool_name"],
            # Add more as needed
        }
        
        return required_params_map.get((framework, action), [])
        
    def _get_parameter_types(self, framework: str, action: str) -> Dict[str, type]:
        """Get parameter types for an action."""
        # This would be populated from framework metadata
        param_types_map = {
            ("langchain", "analyze_sentiment"): {
                "text": str,
                "model": str,
                "temperature": float
            },
            ("temporal", "start_workflow"): {
                "workflow_name": str,
                "parameters": dict
            },
            # Add more as needed
        }
        
        return param_types_map.get((framework, action), {})
        
    def _find_redundant_conditions(self, conditions: List[RuleCondition]) -> List[Tuple[RuleCondition, RuleCondition]]:
        """Find redundant conditions."""
        redundant = []
        
        for i, cond1 in enumerate(conditions):
            for j, cond2 in enumerate(conditions[i+1:], i+1):
                if self._are_conditions_redundant(cond1, cond2):
                    redundant.append((cond1, cond2))
                    
        return redundant
        
    def _are_conditions_redundant(self, cond1: RuleCondition, cond2: RuleCondition) -> bool:
        """Check if two conditions are redundant."""
        if cond1.field != cond2.field:
            return False
            
        # Same condition
        if cond1.operator == cond2.operator and cond1.value == cond2.value:
            return True
            
        # Subset conditions
        if cond1.operator == "greater_than" and cond2.operator == "greater_or_equal":
            if isinstance(cond1.value, (int, float)) and isinstance(cond2.value, (int, float)):
                return cond1.value >= cond2.value
                
        return False
        
    def _find_contradictory_conditions(self, conditions: List[RuleCondition]) -> List[Tuple[RuleCondition, RuleCondition]]:
        """Find contradictory conditions."""
        contradictions = []
        
        for i, cond1 in enumerate(conditions):
            for j, cond2 in enumerate(conditions[i+1:], i+1):
                if self._are_conditions_contradictory(cond1, cond2):
                    contradictions.append((cond1, cond2))
                    
        return contradictions
        
    def _are_conditions_contradictory(self, cond1: RuleCondition, cond2: RuleCondition) -> bool:
        """Check if two conditions are contradictory."""
        if cond1.field != cond2.field:
            return False
            
        # Direct contradictions
        if cond1.operator == "equals" and cond2.operator == "not_equals":
            return cond1.value == cond2.value
            
        # Range contradictions
        if cond1.operator == "greater_than" and cond2.operator == "less_than":
            if isinstance(cond1.value, (int, float)) and isinstance(cond2.value, (int, float)):
                return cond1.value >= cond2.value
                
        return False
        
    def _check_injection_risks(self, parameters: Dict[str, Any]) -> List[str]:
        """Check for potential injection risks in parameters."""
        risks = []
        
        injection_patterns = [
            r'[;\'"]',  # SQL injection indicators
            r'<script',  # XSS indicators
            r'\$\{',     # Template injection
            r'`',        # Command injection
        ]
        
        for param, value in parameters.items():
            if isinstance(value, str):
                for pattern in injection_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        risks.append(param)
                        break
                        
        return risks
        
    def _has_sequential_dependencies(self, actions: List[RuleAction]) -> bool:
        """Check if actions have sequential dependencies."""
        # Simple heuristic: check if action outputs are used as inputs
        output_patterns = ["create", "generate", "produce", "output"]
        input_patterns = ["use", "process", "analyze", "input"]
        
        has_outputs = any(
            any(pattern in action.action.lower() for pattern in output_patterns)
            for action in actions
        )
        
        has_inputs = any(
            any(pattern in action.action.lower() for pattern in input_patterns)
            for action in actions
        )
        
        return has_outputs and has_inputs
        
    def _is_action_supported(self, action: str, capabilities: List[FrameworkCapability]) -> bool:
        """Check if action is supported by framework capabilities."""
        # Simple check - would be more sophisticated in production
        for capability in capabilities:
            if action.lower() in capability.value.lower():
                return True
        return False


from typing import Callable