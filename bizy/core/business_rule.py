"""
Business Rule: Framework-agnostic business logic definition.

This module provides the base classes and patterns for defining business rules
that can be executed across multiple AI frameworks.
"""

from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import uuid


class RuleType(Enum):
    """Types of business rules supported by the orchestrator."""
    CONDITION = "condition"
    ACTION = "action"
    WORKFLOW = "workflow"
    POLICY = "policy"


class RulePriority(Enum):
    """Priority levels for rule execution."""
    LOW = 1
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 15


@dataclass
class RuleCondition:
    """Represents a condition that must be met for rule execution."""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, contains, etc.
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against the provided context."""
        field_value = self._get_field_value(context, self.field)

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "ne":
            return field_value != self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "contains":
            return self.value in field_value
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")

    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """Extract field value from context, supporting nested field access."""
        parts = field.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value


@dataclass
class RuleAction:
    """Represents an action to be executed when rule conditions are met."""
    framework: str
    action: str
    parameters: Dict[str, Any]
    timeout: Optional[float] = None
    retry_count: int = 0


class BusinessRule:
    """
    Framework-agnostic business rule that can be executed across multiple AI frameworks.

    A BusinessRule defines:
    - Conditions that determine when the rule should execute
    - Actions that should be performed when conditions are met
    - Metadata for rule management and coordination
    """

    def __init__(
        self,
        name: str,
        rule_type: RuleType = RuleType.CONDITION,
        priority: RulePriority = RulePriority.MEDIUM,
        conditions: Optional[List[RuleCondition]] = None,
        actions: Optional[List[RuleAction]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.rule_type = rule_type
        self.priority = priority
        self.conditions = conditions or []
        self.actions = actions or []
        self.description = description
        self.metadata = metadata or {}

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """
        Determine if this rule should execute based on the provided context.

        Args:
            context: Execution context containing relevant data

        Returns:
            True if all conditions are met, False otherwise
        """
        if not self.conditions:
            return True

        # All conditions must be met for rule execution
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False

        return True

    def get_applicable_actions(self, frameworks: List[str]) -> List[RuleAction]:
        """
        Get actions that can be executed on the provided frameworks.

        Args:
            frameworks: List of available framework names

        Returns:
            List of actions applicable to available frameworks
        """
        applicable_actions = []

        for action in self.actions:
            if action.framework in frameworks:
                applicable_actions.append(action)

        return applicable_actions

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type.value,
            "priority": self.priority.value,
            "conditions": [
                {
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value
                }
                for c in self.conditions
            ],
            "actions": [
                {
                    "framework": a.framework,
                    "action": a.action,
                    "parameters": a.parameters,
                    "timeout": a.timeout,
                    "retry_count": a.retry_count
                }
                for a in self.actions
            ],
            "description": self.description,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessRule":
        """Create BusinessRule from dictionary representation."""
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(RuleCondition(
                field=cond_data["field"],
                operator=cond_data["operator"],
                value=cond_data["value"]
            ))

        actions = []
        for action_data in data.get("actions", []):
            actions.append(RuleAction(
                framework=action_data["framework"],
                action=action_data["action"],
                parameters=action_data["parameters"],
                timeout=action_data.get("timeout"),
                retry_count=action_data.get("retry_count", 0)
            ))

        rule = cls(
            name=data["name"],
            rule_type=RuleType(data.get("rule_type", "condition")),
            priority=RulePriority(data.get("priority", 5)),
            conditions=conditions,
            actions=actions,
            description=data.get("description"),
            metadata=data.get("metadata", {})
        )

        # Set ID if provided
        if "id" in data:
            rule.id = data["id"]

        return rule


class RuleConflictResolver:
    """Resolves conflicts between multiple business rules."""

    @staticmethod
    def resolve_conflicts(rules: List[BusinessRule]) -> List[BusinessRule]:
        """
        Resolve conflicts between rules based on priority and rule type.

        Args:
            rules: List of potentially conflicting rules

        Returns:
            List of rules with conflicts resolved
        """
        # Sort by priority (highest first)
        sorted_rules = sorted(
            rules, key=lambda r: r.priority.value, reverse=True)

        # For now, simple priority-based resolution
        # More sophisticated conflict resolution can be added later
        return sorted_rules
