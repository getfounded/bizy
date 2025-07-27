"""Tests for BusinessRule class."""

import pytest
from bizy.core.business_rule import (
    BusinessRule, RuleType, RulePriority, RuleCondition, RuleAction, RuleConflictResolver
)


class TestRuleCondition:
    """Test cases for RuleCondition."""
    
    def test_evaluate_equals(self):
        """Test equals operator."""
        condition = RuleCondition("status", "eq", "active")
        assert condition.evaluate({"status": "active"}) is True
        assert condition.evaluate({"status": "inactive"}) is False
        
    def test_evaluate_not_equals(self):
        """Test not equals operator."""
        condition = RuleCondition("status", "ne", "active")
        assert condition.evaluate({"status": "inactive"}) is True
        assert condition.evaluate({"status": "active"}) is False
        
    def test_evaluate_greater_than(self):
        """Test greater than operator."""
        condition = RuleCondition("score", "gt", 50)
        assert condition.evaluate({"score": 60}) is True
        assert condition.evaluate({"score": 40}) is False
        
    def test_evaluate_less_than(self):
        """Test less than operator."""
        condition = RuleCondition("score", "lt", 50)
        assert condition.evaluate({"score": 40}) is True
        assert condition.evaluate({"score": 60}) is False
        
    def test_evaluate_in(self):
        """Test in operator."""
        condition = RuleCondition("category", "in", ["gold", "platinum"])
        assert condition.evaluate({"category": "gold"}) is True
        assert condition.evaluate({"category": "silver"}) is False
        
    def test_evaluate_contains(self):
        """Test contains operator."""
        condition = RuleCondition("message", "contains", "error")
        assert condition.evaluate({"message": "An error occurred"}) is True
        assert condition.evaluate({"message": "Success"}) is False
        
    def test_evaluate_nested_field(self):
        """Test evaluation of nested fields."""
        condition = RuleCondition("user.tier", "eq", "premium")
        context = {"user": {"tier": "premium", "name": "John"}}
        assert condition.evaluate(context) is True
        
    def test_evaluate_missing_field(self):
        """Test evaluation when field is missing."""
        condition = RuleCondition("missing_field", "eq", "value")
        assert condition.evaluate({}) is False


class TestBusinessRule:
    """Test cases for BusinessRule."""
    
    def test_rule_creation(self):
        """Test creating a business rule."""
        rule = BusinessRule(
            name="test_rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.HIGH
        )
        
        assert rule.name == "test_rule"
        assert rule.rule_type == RuleType.CONDITION
        assert rule.priority == RulePriority.HIGH
        assert rule.id is not None
        
    def test_should_execute_no_conditions(self):
        """Test should_execute with no conditions."""
        rule = BusinessRule(name="test_rule")
        assert rule.should_execute({}) is True
        
    def test_should_execute_with_conditions(self):
        """Test should_execute with conditions."""
        conditions = [
            RuleCondition("status", "eq", "active"),
            RuleCondition("score", "gt", 50)
        ]
        rule = BusinessRule(name="test_rule", conditions=conditions)
        
        # All conditions met
        assert rule.should_execute({"status": "active", "score": 60}) is True
        
        # One condition not met
        assert rule.should_execute({"status": "active", "score": 40}) is False
        assert rule.should_execute({"status": "inactive", "score": 60}) is False
        
    def test_get_applicable_actions(self):
        """Test getting applicable actions for available frameworks."""
        actions = [
            RuleAction("langchain", "analyze", {"prompt": "Analyze this"}),
            RuleAction("temporal", "workflow", {"name": "process"}),
            RuleAction("mcp", "tool", {"tool_id": "calculator"})
        ]
        rule = BusinessRule(name="test_rule", actions=actions)
        
        # Test with all frameworks available
        applicable = rule.get_applicable_actions(["langchain", "temporal", "mcp"])
        assert len(applicable) == 3
        
        # Test with subset of frameworks
        applicable = rule.get_applicable_actions(["langchain", "temporal"])
        assert len(applicable) == 2
        assert all(a.framework in ["langchain", "temporal"] for a in applicable)
        
    def test_to_dict(self):
        """Test converting rule to dictionary."""
        conditions = [RuleCondition("status", "eq", "active")]
        actions = [RuleAction("langchain", "analyze", {"prompt": "test"})]
        
        rule = BusinessRule(
            name="test_rule",
            rule_type=RuleType.ACTION,
            priority=RulePriority.MEDIUM,
            conditions=conditions,
            actions=actions,
            description="Test rule",
            metadata={"version": 1}
        )
        
        rule_dict = rule.to_dict()
        
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["rule_type"] == "action"
        assert rule_dict["priority"] == 5
        assert len(rule_dict["conditions"]) == 1
        assert len(rule_dict["actions"]) == 1
        assert rule_dict["description"] == "Test rule"
        assert rule_dict["metadata"]["version"] == 1
        
    def test_from_dict(self):
        """Test creating rule from dictionary."""
        rule_data = {
            "name": "test_rule",
            "rule_type": "workflow",
            "priority": 10,
            "conditions": [
                {"field": "status", "operator": "eq", "value": "active"}
            ],
            "actions": [
                {
                    "framework": "temporal",
                    "action": "start_workflow",
                    "parameters": {"workflow_id": "test"},
                    "timeout": 30.0,
                    "retry_count": 3
                }
            ],
            "description": "Test workflow rule",
            "metadata": {"category": "test"}
        }
        
        rule = BusinessRule.from_dict(rule_data)
        
        assert rule.name == "test_rule"
        assert rule.rule_type == RuleType.WORKFLOW
        assert rule.priority == RulePriority.HIGH
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1
        assert rule.actions[0].timeout == 30.0
        assert rule.actions[0].retry_count == 3


class TestRuleConflictResolver:
    """Test cases for RuleConflictResolver."""
    
    def test_resolve_conflicts_by_priority(self):
        """Test conflict resolution based on priority."""
        rules = [
            BusinessRule("low_priority", priority=RulePriority.LOW),
            BusinessRule("critical", priority=RulePriority.CRITICAL),
            BusinessRule("medium", priority=RulePriority.MEDIUM),
            BusinessRule("high", priority=RulePriority.HIGH)
        ]
        
        resolved = RuleConflictResolver.resolve_conflicts(rules)
        
        # Should be sorted by priority (highest first)
        assert resolved[0].name == "critical"
        assert resolved[1].name == "high"
        assert resolved[2].name == "medium"
        assert resolved[3].name == "low_priority"