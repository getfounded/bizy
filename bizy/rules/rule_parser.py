"""
Rule Parser: Parses YAML-based business rule definitions.

This module provides functionality to parse YAML rule definitions into
internal business rule objects that can be executed across frameworks.
"""

from typing import Any, Dict, List, Optional, Union
import yaml
import logging
from pathlib import Path

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction
from ..core.framework_adapter import FrameworkCapability

logger = logging.getLogger(__name__)


class RuleParseError(Exception):
    """Raised when rule parsing fails."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.line = line
        self.column = column
        super().__init__(f"Rule parse error at line {line}, column {column}: {message}" if line else message)


class RuleParser:
    """
    Parses YAML-based business rule definitions.
    
    Example YAML rule:
    ```yaml
    rule: customer_escalation
    name: Premium Customer Escalation
    description: Escalate premium customers with negative sentiment
    priority: high
    enabled: true
    
    conditions:
      all:
        - field: sentiment_score
          operator: less_than
          value: 0.3
        - field: customer_tier
          operator: equals
          value: premium
          
    actions:
      - framework: langchain
        action: analyze_sentiment_details
        parameters:
          model: gpt-4
          temperature: 0.2
      - framework: temporal
        action: start_escalation_workflow
        parameters:
          workflow_name: customer_escalation
          priority: high
      - framework: mcp_toolkit
        action: notify_account_manager
        parameters:
          notification_type: urgent
          
    error_handling:
      retry_count: 3
      fallback_rule: standard_escalation
      
    metadata:
      author: system
      version: "1.0"
      tags: [customer_service, escalation, premium]
    ```
    """
    
    def __init__(self):
        self.supported_operators = {
            "equals", "not_equals", "greater_than", "less_than",
            "greater_or_equal", "less_or_equal", "contains", "not_contains",
            "starts_with", "ends_with", "regex", "in", "not_in"
        }
        self.supported_condition_combinators = {"all", "any", "not"}
        
    def parse_file(self, file_path: Union[str, Path]) -> BusinessRule:
        """
        Parse a YAML rule file.
        
        Args:
            file_path: Path to YAML rule file
            
        Returns:
            Parsed BusinessRule object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise RuleParseError(f"Rule file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return self.parse_string(content, source_file=str(file_path))
        except yaml.YAMLError as e:
            raise RuleParseError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise RuleParseError(f"Error reading rule file {file_path}: {e}")
            
    def parse_string(self, yaml_content: str, source_file: Optional[str] = None) -> BusinessRule:
        """
        Parse a YAML rule string.
        
        Args:
            yaml_content: YAML rule content
            source_file: Optional source file path for error reporting
            
        Returns:
            Parsed BusinessRule object
        """
        try:
            # Load YAML with line number tracking
            loader = yaml.SafeLoader(yaml_content)
            loader.check_node = lambda: None  # Disable duplicate key checking
            data = yaml.load(yaml_content, Loader=yaml.SafeLoader)
            
            if not isinstance(data, dict):
                raise RuleParseError("Rule must be a YAML object/dictionary")
                
            return self._parse_rule_dict(data, source_file)
            
        except yaml.YAMLError as e:
            # Extract line/column info if available
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                raise RuleParseError(str(e), line=mark.line + 1, column=mark.column + 1)
            raise RuleParseError(f"YAML parsing error: {e}")
            
    def parse_batch(self, yaml_content: str) -> List[BusinessRule]:
        """
        Parse multiple rules from a single YAML document.
        
        Args:
            yaml_content: YAML content with multiple rules
            
        Returns:
            List of parsed BusinessRule objects
        """
        try:
            documents = list(yaml.safe_load_all(yaml_content))
            rules = []
            
            for i, doc in enumerate(documents):
                if not isinstance(doc, dict):
                    raise RuleParseError(f"Document {i+1} must be a YAML object")
                    
                rule = self._parse_rule_dict(doc, source_doc=i+1)
                rules.append(rule)
                
            return rules
            
        except yaml.YAMLError as e:
            raise RuleParseError(f"YAML parsing error: {e}")
            
    def _parse_rule_dict(
        self,
        data: Dict[str, Any],
        source_file: Optional[str] = None,
        source_doc: Optional[int] = None
    ) -> BusinessRule:
        """Parse rule from dictionary."""
        # Extract basic fields
        rule_id = data.get("rule", data.get("id"))
        if not rule_id:
            raise RuleParseError("Missing required field 'rule' or 'id'")
            
        name = data.get("name", rule_id)
        description = data.get("description", "")
        priority = data.get("priority", "medium")
        enabled = data.get("enabled", True)
        
        # Parse conditions
        conditions = self._parse_conditions(data.get("conditions", {}))
        
        # Parse actions
        actions = self._parse_actions(data.get("actions", []))
        
        # Create rule
        rule = BusinessRule(
            id=rule_id,
            name=name,
            description=description,
            priority=priority,
            enabled=enabled
        )
        
        # Add conditions and actions
        for condition in conditions:
            rule.add_condition(condition)
            
        for action in actions:
            rule.add_action(action)
            
        # Parse error handling
        if "error_handling" in data:
            self._parse_error_handling(rule, data["error_handling"])
            
        # Parse metadata
        if "metadata" in data:
            rule.metadata = data["metadata"]
            
        # Add source info
        if source_file:
            rule.metadata["source_file"] = source_file
        if source_doc:
            rule.metadata["source_document"] = source_doc
            
        return rule
        
    def _parse_conditions(self, conditions_data: Union[Dict, List]) -> List[RuleCondition]:
        """Parse conditions section."""
        if not conditions_data:
            return []
            
        conditions = []
        
        # Handle different condition formats
        if isinstance(conditions_data, list):
            # Simple list of conditions (implicit AND)
            for cond_data in conditions_data:
                condition = self._parse_single_condition(cond_data)
                conditions.append(condition)
                
        elif isinstance(conditions_data, dict):
            # Complex conditions with combinators
            conditions = self._parse_complex_conditions(conditions_data)
            
        else:
            raise RuleParseError(f"Invalid conditions format: {type(conditions_data)}")
            
        return conditions
        
    def _parse_single_condition(self, cond_data: Dict[str, Any]) -> RuleCondition:
        """Parse a single condition."""
        field = cond_data.get("field")
        if not field:
            raise RuleParseError("Condition missing required field 'field'")
            
        operator = cond_data.get("operator", "equals")
        if operator not in self.supported_operators:
            raise RuleParseError(f"Unsupported operator: {operator}")
            
        value = cond_data.get("value")
        if value is None:
            raise RuleParseError("Condition missing required field 'value'")
            
        # Create condition
        condition = RuleCondition(field, operator, value)
        
        # Add optional fields
        if "description" in cond_data:
            condition.description = cond_data["description"]
        if "case_sensitive" in cond_data:
            condition.case_sensitive = cond_data["case_sensitive"]
            
        return condition
        
    def _parse_complex_conditions(self, conditions_data: Dict[str, Any]) -> List[RuleCondition]:
        """Parse complex conditions with combinators."""
        conditions = []
        
        for combinator, cond_list in conditions_data.items():
            if combinator not in self.supported_condition_combinators:
                # Treat as single condition dict
                condition = self._parse_single_condition(conditions_data)
                return [condition]
                
            if not isinstance(cond_list, list):
                raise RuleParseError(f"Combinator '{combinator}' must have a list value")
                
            # Parse each condition in the group
            group_conditions = []
            for cond_data in cond_list:
                if isinstance(cond_data, dict) and any(
                    k in cond_data for k in self.supported_condition_combinators
                ):
                    # Nested complex condition
                    nested = self._parse_complex_conditions(cond_data)
                    group_conditions.extend(nested)
                else:
                    # Simple condition
                    condition = self._parse_single_condition(cond_data)
                    group_conditions.append(condition)
                    
            # Store combinator info in conditions
            for condition in group_conditions:
                condition.combinator = combinator
                
            conditions.extend(group_conditions)
            
        return conditions
        
    def _parse_actions(self, actions_data: List[Dict[str, Any]]) -> List[RuleAction]:
        """Parse actions section."""
        if not actions_data:
            raise RuleParseError("Rule must have at least one action")
            
        if not isinstance(actions_data, list):
            raise RuleParseError("Actions must be a list")
            
        actions = []
        
        for i, action_data in enumerate(actions_data):
            if not isinstance(action_data, dict):
                raise RuleParseError(f"Action {i+1} must be a dictionary")
                
            framework = action_data.get("framework")
            if not framework:
                raise RuleParseError(f"Action {i+1} missing required field 'framework'")
                
            action_name = action_data.get("action")
            if not action_name:
                raise RuleParseError(f"Action {i+1} missing required field 'action'")
                
            # Create action
            action = RuleAction(framework, action_name)
            
            # Add parameters
            if "parameters" in action_data:
                action.parameters = action_data["parameters"]
                
            # Add optional fields
            if "timeout" in action_data:
                action.timeout = action_data["timeout"]
            if "retry_count" in action_data:
                action.retry_count = action_data["retry_count"]
            if "continue_on_error" in action_data:
                action.continue_on_error = action_data["continue_on_error"]
            if "description" in action_data:
                action.description = action_data["description"]
                
            actions.append(action)
            
        return actions
        
    def _parse_error_handling(self, rule: BusinessRule, error_data: Dict[str, Any]):
        """Parse error handling configuration."""
        if "retry_count" in error_data:
            rule.retry_count = error_data["retry_count"]
            
        if "fallback_rule" in error_data:
            rule.fallback_rule = error_data["fallback_rule"]
            
        if "error_threshold" in error_data:
            rule.error_threshold = error_data["error_threshold"]
            
        if "notification_channels" in error_data:
            rule.notification_channels = error_data["notification_channels"]
            
    def validate_syntax(self, yaml_content: str) -> List[str]:
        """
        Validate YAML syntax without fully parsing.
        
        Args:
            yaml_content: YAML content to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Try to load YAML
            data = yaml.safe_load(yaml_content)
            
            if not isinstance(data, dict):
                errors.append("Root element must be a YAML object")
                return errors
                
            # Check required fields
            if "rule" not in data and "id" not in data:
                errors.append("Missing required field 'rule' or 'id'")
                
            if "actions" not in data:
                errors.append("Missing required field 'actions'")
            elif not isinstance(data["actions"], list):
                errors.append("Field 'actions' must be a list")
            elif len(data["actions"]) == 0:
                errors.append("Must have at least one action")
                
            # Check conditions format
            if "conditions" in data:
                cond = data["conditions"]
                if not isinstance(cond, (dict, list)):
                    errors.append("Field 'conditions' must be a dictionary or list")
                    
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
            
        return errors
        
    def to_yaml(self, rule: BusinessRule) -> str:
        """
        Convert a BusinessRule back to YAML format.
        
        Args:
            rule: BusinessRule to convert
            
        Returns:
            YAML string representation
        """
        data = {
            "rule": rule.id,
            "name": rule.name,
            "description": rule.description,
            "priority": rule.priority,
            "enabled": rule.enabled
        }
        
        # Convert conditions
        if rule.conditions:
            conditions = []
            for condition in rule.conditions:
                cond_dict = {
                    "field": condition.field,
                    "operator": condition.operator,
                    "value": condition.value
                }
                if condition.description:
                    cond_dict["description"] = condition.description
                conditions.append(cond_dict)
                
            # Group by combinator if needed
            if len(set(c.combinator for c in rule.conditions)) > 1:
                # Complex conditions with multiple combinators
                grouped = {}
                for condition in rule.conditions:
                    combinator = condition.combinator or "all"
                    if combinator not in grouped:
                        grouped[combinator] = []
                    grouped[combinator].append({
                        "field": condition.field,
                        "operator": condition.operator,
                        "value": condition.value
                    })
                data["conditions"] = grouped
            else:
                data["conditions"] = conditions
                
        # Convert actions
        actions = []
        for action in rule.actions:
            act_dict = {
                "framework": action.framework,
                "action": action.action
            }
            if action.parameters:
                act_dict["parameters"] = action.parameters
            if action.timeout:
                act_dict["timeout"] = action.timeout
            if action.retry_count:
                act_dict["retry_count"] = action.retry_count
            if action.description:
                act_dict["description"] = action.description
            actions.append(act_dict)
            
        data["actions"] = actions
        
        # Add error handling
        error_handling = {}
        if rule.retry_count:
            error_handling["retry_count"] = rule.retry_count
        if rule.fallback_rule:
            error_handling["fallback_rule"] = rule.fallback_rule
        if error_handling:
            data["error_handling"] = error_handling
            
        # Add metadata
        if rule.metadata:
            data["metadata"] = rule.metadata
            
        # Convert to YAML
        return yaml.dump(data, default_flow_style=False, sort_keys=False)