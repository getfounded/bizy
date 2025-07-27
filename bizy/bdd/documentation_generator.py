"""
BDD Documentation Generator: Converts BusinessRule objects to natural language.

This module generates business-stakeholder-friendly documentation from BusinessRule
objects, creating living documentation that stays current with implementation.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction, RuleType, RulePriority


class BDDDocumentationGenerator:
    """
    Generates BDD scenarios and documentation from BusinessRule objects.
    
    Converts technical business rules back into natural language
    for stakeholder review and documentation.
    """
    
    def __init__(self):
        self.framework_display_names = {
            'langchain': 'LangChain',
            'semantic_kernel': 'Semantic Kernel',
            'mcp': 'MCP toolkit',
            'temporal': 'Temporal',
            'fastmcp': 'FastMCP',
            'zep': 'Zep'
        }
        
    def generate_scenario(self, rule: BusinessRule) -> str:
        """Generate a Gherkin scenario from a BusinessRule."""
        scenario_lines = [f"  Scenario: {rule.name}"]
        
        # Add description as comment if available
        if rule.description and rule.description != f"Generated from Gherkin scenario: {rule.name}":
            scenario_lines.append(f"    # {rule.description}")
            
        # Generate Given statements from conditions
        for i, condition in enumerate(rule.conditions):
            given_text = self._condition_to_given(condition)
            keyword = "Given" if i == 0 else "And"
            scenario_lines.append(f"    {keyword} {given_text}")
            
        # Add a When statement (trigger)
        when_statement = self._generate_when_statement(rule)
        scenario_lines.append(f"    When {when_statement}")
        
        # Generate Then statements from actions
        for i, action in enumerate(rule.actions):
            then_text = self._action_to_then(action)
            keyword = "Then" if i == 0 else "And"
            scenario_lines.append(f"    {keyword} {then_text}")
            
        return '\n'.join(scenario_lines)
        
    def generate_feature_file(self, rules: List[BusinessRule], feature_name: str, 
                            feature_description: str = None) -> str:
        """Generate a complete Gherkin feature file from multiple business rules."""
        lines = [
            f"Feature: {feature_name}"
        ]
        
        if feature_description:
            lines.extend([
                f"  {line}" for line in feature_description.split('\n')
            ])
        else:
            lines.append("  Business logic automation scenarios")
            
        lines.append("")
        
        # Group rules by type for better organization
        rule_groups = self._group_rules_by_type(rules)
        
        for rule_type, type_rules in rule_groups.items():
            if type_rules:
                lines.append(f"  # {rule_type.title()} Rules")
                lines.append("")
                
                for rule in type_rules:
                    scenario = self.generate_scenario(rule)
                    lines.append(scenario)
                    lines.append("")
                    
        return '\n'.join(lines)
        
    def generate_business_process_documentation(self, rules: List[BusinessRule], 
                                              title: str = "Business Process Documentation") -> str:
        """Generate comprehensive business process documentation."""
        doc_lines = [
            f"# {title}",
            "",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Business Rules: {len(rules)}",
            "",
            "## Overview",
            "",
            "This document describes the automated business logic that coordinates",
            "AI systems to implement business processes. Each scenario represents",
            "an executable business rule that can be triggered by specific conditions.",
            "",
        ]
        
        # Statistics section
        stats = self._generate_rule_statistics(rules)
        doc_lines.extend([
            "## Statistics",
            "",
            f"- **Total Rules**: {stats['total_rules']}",
            f"- **High Priority Rules**: {stats['high_priority']}",
            f"- **Workflow Rules**: {stats['workflow_rules']}",
            f"- **Frameworks Used**: {', '.join(stats['frameworks_used'])}",
            f"- **Average Conditions per Rule**: {stats['avg_conditions']:.1f}",
            f"- **Average Actions per Rule**: {stats['avg_actions']:.1f}",
            "",
        ])
        
        # Rules by priority
        priority_groups = self._group_rules_by_priority(rules)
        
        for priority in [RulePriority.CRITICAL, RulePriority.HIGH, RulePriority.MEDIUM, RulePriority.LOW]:
            if priority in priority_groups and priority_groups[priority]:
                doc_lines.extend([
                    f"## {priority.name.title()} Priority Rules",
                    "",
                ])
                
                for rule in priority_groups[priority]:
                    doc_lines.extend(self._generate_rule_documentation(rule))
                    doc_lines.append("")
                    
        # Framework usage section
        doc_lines.extend([
            "## Framework Coordination Patterns",
            "",
            "The following patterns show how different AI frameworks are coordinated:",
            "",
        ])
        
        framework_patterns = self._analyze_framework_patterns(rules)
        for pattern, count in framework_patterns.items():
            doc_lines.append(f"- **{pattern}**: Used in {count} rule(s)")
            
        return '\n'.join(doc_lines)
        
    def generate_stakeholder_summary(self, rules: List[BusinessRule]) -> str:
        """Generate an executive summary for business stakeholders."""
        total_rules = len(rules)
        high_priority = len([r for r in rules if r.priority in [RulePriority.CRITICAL, RulePriority.HIGH]])
        frameworks = set()
        
        for rule in rules:
            for action in rule.actions:
                frameworks.add(action.framework)
                
        summary_lines = [
            "# Business Logic Automation Summary",
            "",
            "## Key Metrics",
            f"- **{total_rules}** automated business rules are active",
            f"- **{high_priority}** rules are high or critical priority",
            f"- **{len(frameworks)}** AI systems are coordinated",
            "",
            "## Business Impact",
            "- Automated decision making reduces manual intervention",
            "- Cross-system coordination ensures consistent outcomes",
            "- Priority-based execution handles urgent scenarios first",
            "- Natural language rules enable business team involvement",
            "",
            "## AI Systems Involved",
        ]
        
        for framework in sorted(frameworks):
            display_name = self.framework_display_names.get(framework, framework)
            rule_count = sum(1 for rule in rules for action in rule.actions if action.framework == framework)
            summary_lines.append(f"- **{display_name}**: Used in {rule_count} business rule(s)")
            
        summary_lines.extend([
            "",
            "## Sample Business Scenarios",
            "",
        ])
        
        # Include a few example scenarios
        sample_rules = sorted(rules, key=lambda r: r.priority.value, reverse=True)[:3]
        for rule in sample_rules:
            summary_lines.append(f"### {rule.name}")
            summary_lines.append(f"*Priority: {rule.priority.name}*")
            summary_lines.append("")
            summary_lines.append(self._generate_plain_language_summary(rule))
            summary_lines.append("")
            
        return '\n'.join(summary_lines)
        
    def _condition_to_given(self, condition: RuleCondition) -> str:
        """Convert a RuleCondition to natural language Given statement."""
        field_display = condition.field.replace('_', ' ').replace('.', ' ')
        
        if condition.operator == "eq":
            if isinstance(condition.value, bool):
                return f"{field_display} is {'enabled' if condition.value else 'disabled'}"
            else:
                return f"{field_display} equals '{condition.value}'"
        elif condition.operator == "lt":
            return f"the {field_display} is below {condition.value}"
        elif condition.operator == "gt":
            return f"the {field_display} is above {condition.value}"
        elif condition.operator == "lte":
            return f"the {field_display} is at most {condition.value}"
        elif condition.operator == "gte":
            return f"the {field_display} is at least {condition.value}"
        elif condition.operator == "in":
            values = "', '".join(str(v) for v in condition.value)
            return f"the {field_display} is one of '{values}'"
        elif condition.operator == "contains":
            return f"the {field_display} contains '{condition.value}'"
        else:
            return f"the {field_display} {condition.operator} {condition.value}"
            
    def _action_to_then(self, action: RuleAction) -> str:
        """Convert a RuleAction to natural language Then statement."""
        framework_display = self.framework_display_names.get(action.framework, action.framework)
        action_display = action.action.replace('_', ' ')
        
        # Common action patterns
        if action.action.startswith('start_'):
            return f"start {action_display[6:]} using {framework_display}"
        elif action.action.startswith('create_'):
            return f"create {action_display[7:]} using {framework_display}"
        elif action.action.startswith('execute_'):
            return f"execute {action_display[8:]} using {framework_display}"
        elif action.action.startswith('analyze_'):
            return f"analyze {action_display[8:]} using {framework_display}"
        else:
            return f"the system should {action_display} using {framework_display}"
            
    def _generate_when_statement(self, rule: BusinessRule) -> str:
        """Generate appropriate When statement based on rule type and conditions."""
        if rule.rule_type == RuleType.WORKFLOW:
            return "the business process is triggered"
        elif rule.rule_type == RuleType.POLICY:
            return "the policy conditions are evaluated"
        elif rule.rule_type == RuleType.ACTION:
            return "the action is requested"
        else:
            return "the business rule is triggered"
            
    def _group_rules_by_type(self, rules: List[BusinessRule]) -> Dict[str, List[BusinessRule]]:
        """Group rules by their type."""
        groups = {}
        for rule in rules:
            rule_type = rule.rule_type.value
            if rule_type not in groups:
                groups[rule_type] = []
            groups[rule_type].append(rule)
            
        return groups
        
    def _group_rules_by_priority(self, rules: List[BusinessRule]) -> Dict[RulePriority, List[BusinessRule]]:
        """Group rules by priority level."""
        groups = {}
        for rule in rules:
            if rule.priority not in groups:
                groups[rule.priority] = []
            groups[rule.priority].append(rule)
            
        return groups
        
    def _generate_rule_documentation(self, rule: BusinessRule) -> List[str]:
        """Generate detailed documentation for a single rule."""
        lines = [
            f"### {rule.name}",
            f"**Type**: {rule.rule_type.value.title()}  ",
            f"**Priority**: {rule.priority.name}  ",
        ]
        
        if rule.description:
            lines.append(f"**Description**: {rule.description}  ")
            
        lines.append("")
        lines.append("**Conditions**:")
        if rule.conditions:
            for condition in rule.conditions:
                condition_text = self._condition_to_given(condition)
                lines.append(f"- {condition_text}")
        else:
            lines.append("- Always execute (no conditions)")
            
        lines.append("")
        lines.append("**Actions**:")
        for action in rule.actions:
            action_text = self._action_to_then(action)
            lines.append(f"- {action_text}")
            
        if rule.metadata and rule.metadata.get('source') != 'gherkin':
            lines.append("")
            lines.append("**Technical Details**:")
            lines.append(f"- Rule ID: `{rule.id}`")
            lines.append(f"- Framework Actions: {len(rule.actions)}")
            
        return lines
        
    def _generate_rule_statistics(self, rules: List[BusinessRule]) -> Dict[str, Any]:
        """Generate statistics about the rules."""
        if not rules:
            return {
                'total_rules': 0,
                'high_priority': 0,
                'workflow_rules': 0,
                'frameworks_used': [],
                'avg_conditions': 0,
                'avg_actions': 0
            }
            
        high_priority = len([r for r in rules if r.priority in [RulePriority.CRITICAL, RulePriority.HIGH]])
        workflow_rules = len([r for r in rules if r.rule_type == RuleType.WORKFLOW])
        
        frameworks = set()
        total_conditions = 0
        total_actions = 0
        
        for rule in rules:
            total_conditions += len(rule.conditions)
            total_actions += len(rule.actions)
            for action in rule.actions:
                frameworks.add(action.framework)
                
        return {
            'total_rules': len(rules),
            'high_priority': high_priority,
            'workflow_rules': workflow_rules,
            'frameworks_used': sorted(frameworks),
            'avg_conditions': total_conditions / len(rules),
            'avg_actions': total_actions / len(rules)
        }
        
    def _analyze_framework_patterns(self, rules: List[BusinessRule]) -> Dict[str, int]:
        """Analyze common framework coordination patterns."""
        patterns = {}
        
        for rule in rules:
            if len(rule.actions) == 1:
                framework = rule.actions[0].framework
                pattern = f"Single-framework ({self.framework_display_names.get(framework, framework)})"
                patterns[pattern] = patterns.get(pattern, 0) + 1
            elif len(rule.actions) > 1:
                frameworks = [action.framework for action in rule.actions]
                unique_frameworks = list(set(frameworks))
                if len(unique_frameworks) == 1:
                    pattern = f"Multi-action single framework ({self.framework_display_names.get(unique_frameworks[0], unique_frameworks[0])})"
                else:
                    framework_names = [self.framework_display_names.get(f, f) for f in unique_frameworks]
                    pattern = f"Cross-framework coordination ({', '.join(sorted(framework_names))})"
                patterns[pattern] = patterns.get(pattern, 0) + 1
                
        return patterns
        
    def _generate_plain_language_summary(self, rule: BusinessRule) -> str:
        """Generate a plain language summary of what the rule does."""
        lines = []
        
        if rule.conditions:
            condition_summaries = []
            for condition in rule.conditions:
                condition_text = self._condition_to_given(condition)
                condition_summaries.append(condition_text)
            lines.append(f"When {' and '.join(condition_summaries)}, ")
        else:
            lines.append("Whenever triggered, ")
            
        action_summaries = []
        for action in rule.actions:
            action_text = self._action_to_then(action)
            action_summaries.append(action_text)
            
        lines.append(f"the system will {', then '.join(action_summaries)}.")
        
        return ''.join(lines)
        
    def export_to_file(self, content: str, file_path: Path, format: str = "markdown") -> None:
        """Export documentation to a file."""
        if format.lower() == "markdown":
            with open(file_path.with_suffix('.md'), 'w') as f:
                f.write(content)
        elif format.lower() == "html":
            html_content = self._markdown_to_html(content)
            with open(file_path.with_suffix('.html'), 'w') as f:
                f.write(html_content)
        else:
            with open(file_path, 'w') as f:
                f.write(content)
                
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to basic HTML."""
        lines = markdown_content.split('\n')
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Business Logic Documentation</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1, h2, h3 { color: #333; }",
            "code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }",
            "pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }",
            "ul { margin-left: 20px; }",
            "</style>",
            "</head>",
            "<body>",
        ]
        
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('- '):
                html_lines.append(f"<ul><li>{line[2:]}</li></ul>")
            elif line.strip():
                # Simple bold and code formatting
                formatted_line = line.replace('**', '<strong>').replace('**', '</strong>')
                formatted_line = formatted_line.replace('`', '<code>').replace('`', '</code>')
                html_lines.append(f"<p>{formatted_line}</p>")
            else:
                html_lines.append("<br>")
                
        html_lines.extend([
            "</body>",
            "</html>"
        ])
        
        return '\n'.join(html_lines)
