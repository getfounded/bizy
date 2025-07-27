"""
Interactive Scenario Builder CLI

This module provides a command-line interface for business stakeholders to
create BDD scenarios without technical knowledge, with guided prompts and
validation.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import sys

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction, RuleType, RulePriority
from ..bdd.gherkin_parser import GherkinRuleParser, ScenarioTemplateGenerator
from ..bdd.documentation_generator import BDDDocumentationGenerator
from ..bdd.scenario_executor import BDDScenarioExecutor
from ..core.meta_orchestrator import MetaOrchestrator


class InteractiveScenarioBuilder:
    """Interactive CLI for building BDD scenarios with business stakeholders."""
    
    def __init__(self):
        self.parser = GherkinRuleParser()
        self.generator = BDDDocumentationGenerator()
        self.template_generator = ScenarioTemplateGenerator()
        
        # Framework options for business users
        self.framework_options = {
            '1': ('langchain', 'LangChain - Document analysis, content processing'),
            '2': ('semantic_kernel', 'Semantic Kernel - Agent coordination, complex workflows'),
            '3': ('mcp', 'MCP Toolkit - External system integration, tool execution'),
            '4': ('temporal', 'Temporal - Workflow orchestration, process automation'),
            '5': ('fastmcp', 'FastMCP - High-performance data processing'),
            '6': ('zep', 'Zep - Memory management, knowledge storage')
        }
        
        # Common business conditions
        self.condition_templates = {
            '1': ('customer_tier', 'Customer tier/level'),
            '2': ('sentiment_score', 'Customer satisfaction/sentiment'),
            '3': ('account_value', 'Customer account value'),
            '4': ('data_size', 'Data volume/size'),
            '5': ('processing_required', 'Processing requirement flag'),
            '6': ('document_type', 'Document category'),
            '7': ('time_constraint', 'Time-based conditions'),
            '8': ('priority_level', 'Request priority level')
        }
        
        # Common business actions
        self.action_templates = {
            '1': 'analyze_sentiment - Analyze customer sentiment/satisfaction',
            '2': 'start_workflow - Begin business process workflow',
            '3': 'notify_manager - Send notification to manager/supervisor',
            '4': 'escalate_issue - Escalate to higher level support',
            '5': 'process_data - Process/transform data',
            '6': 'extract_information - Extract key information from documents',
            '7': 'store_context - Save information for future reference',
            '8': 'coordinate_agents - Organize multiple AI agents'
        }
        
    def run_interactive_builder(self) -> Optional[str]:
        """Run the interactive scenario builder."""
        print("🎭 Business Logic Scenario Builder")
        print("=" * 50)
        print("Create natural language business rules for AI coordination")
        print()
        
        try:
            # Step 1: Choose creation method
            creation_method = self._choose_creation_method()
            
            if creation_method == 'template':
                return self._build_from_template()
            elif creation_method == 'guided':
                return self._build_with_guidance()
            elif creation_method == 'freeform':
                return self._build_freeform()
            else:
                print("❌ Invalid choice. Exiting.")
                return None
                
        except KeyboardInterrupt:
            print("\n\n👋 Scenario builder cancelled.")
            return None
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None
            
    def _choose_creation_method(self) -> str:
        """Let user choose how to create the scenario."""
        print("How would you like to create your business scenario?")
        print("1. Start with a template (recommended for beginners)")
        print("2. Guided creation with prompts")
        print("3. Free-form writing")
        print()
        
        while True:
            choice = input("Enter your choice (1-3): ").strip()
            if choice == '1':
                return 'template'
            elif choice == '2':
                return 'guided'
            elif choice == '3':
                return 'freeform'
            else:
                print("Please enter 1, 2, or 3")
                
    def _build_from_template(self) -> str:
        """Build scenario starting from a template."""
        print("\n📋 Available Business Process Templates:")
        print("1. Customer Service Automation")
        print("2. Document Processing Workflow")
        print("3. Data Pipeline Management")
        print()
        
        while True:
            choice = input("Choose a template (1-3): ").strip()
            if choice == '1':
                template = self.template_generator.generate_customer_service_template()
                template_name = "Customer Service Automation"
                break
            elif choice == '2':
                template = self.template_generator.generate_document_processing_template()
                template_name = "Document Processing Workflow"
                break
            elif choice == '3':
                template = self.template_generator.generate_data_pipeline_template()
                template_name = "Data Pipeline Management"
                break
            else:
                print("Please enter 1, 2, or 3")
                
        print(f"\n📄 {template_name} Template:")
        print("-" * 40)
        print(template)
        print()
        
        print("💡 This template shows the structure. You can:")
        print("   • Modify the conditions (Given statements)")
        print("   • Change the trigger (When statement)")
        print("   • Adjust the actions (Then statements)")
        print()
        
        customize = input("Would you like to customize this template? (y/n): ").strip().lower()
        if customize == 'y':
            return self._customize_template(template)
        else:
            return template
            
    def _customize_template(self, template: str) -> str:
        """Allow user to customize a template."""
        print("\n🛠️  Template Customization")
        print("Let's personalize this template for your business needs.")
        print()
        
        # Extract scenario name for customization
        lines = template.split('\n')
        scenario_line = None
        for line in lines:
            if line.strip().startswith('Scenario:'):
                scenario_line = line
                break
                
        if scenario_line:
            current_name = scenario_line.split('Scenario:')[1].strip()
            print(f"Current scenario name: {current_name}")
            new_name = input("Enter new scenario name (or press Enter to keep): ").strip()
            if new_name:
                template = template.replace(scenario_line, f"  Scenario: {new_name}")
                
        # Offer to modify specific parts
        print("\nWhat would you like to customize?")
        print("1. Customer conditions (Given statements)")
        print("2. Business triggers (When statements)")
        print("3. System actions (Then statements)")
        print("4. Keep as-is")
        
        choice = input("Choose section to customize (1-4): ").strip()
        
        if choice == '1':
            template = self._customize_conditions(template)
        elif choice == '2':
            template = self._customize_triggers(template)
        elif choice == '3':
            template = self._customize_actions(template)
            
        return template
        
    def _build_with_guidance(self) -> str:
        """Build scenario with step-by-step guidance."""
        print("\n🧭 Guided Scenario Creation")
        print("I'll help you create a business scenario step by step.")
        print()
        
        # Step 1: Scenario name and description
        scenario_name = input("What business process are you automating? (e.g., 'Customer complaint handling'): ").strip()
        
        print("\n📝 Great! Now let's define when this process should trigger...")
        
        # Step 2: Build conditions
        conditions = self._build_conditions_guided()
        
        # Step 3: Define trigger
        print("\n🎯 What event triggers this business process?")
        trigger_options = [
            "a customer interaction is created",
            "a document is uploaded",
            "a data processing request arrives",
            "a support ticket is submitted",
            "a workflow is manually triggered"
        ]
        
        print("Common triggers:")
        for i, option in enumerate(trigger_options, 1):
            print(f"{i}. {option}")
        print("6. Custom trigger")
        
        trigger_choice = input("Choose a trigger (1-6): ").strip()
        if trigger_choice == '6':
            trigger = input("Describe your custom trigger: ").strip()
        else:
            try:
                trigger = trigger_options[int(trigger_choice) - 1]
            except (ValueError, IndexError):
                trigger = "the business rule is triggered"
                
        # Step 4: Build actions
        print("\n⚡ What should happen when these conditions are met?")
        actions = self._build_actions_guided()
        
        # Step 5: Assemble scenario
        scenario = self._assemble_scenario(scenario_name, conditions, trigger, actions)
        
        print("\n✅ Your scenario has been created!")
        print("-" * 40)
        print(scenario)
        
        return scenario
        
    def _build_conditions_guided(self) -> List[str]:
        """Build conditions with guidance."""
        conditions = []
        
        print("\n📋 Let's define the conditions that trigger your business process.")
        print("Available condition types:")
        
        for key, (field, description) in self.condition_templates.items():
            print(f"{key}. {description}")
        print("9. Custom condition")
        print()
        
        while True:
            choice = input("Add a condition (1-9) or 'done' to finish: ").strip()
            
            if choice.lower() == 'done':
                break
                
            if choice == '9':
                custom_condition = input("Describe your condition: ").strip()
                conditions.append(custom_condition)
            elif choice in self.condition_templates:
                field, description = self.condition_templates[choice]
                condition = self._build_specific_condition(field, description)
                if condition:
                    conditions.append(condition)
            else:
                print("Please enter a valid choice (1-9) or 'done'")
                
        return conditions
        
    def _build_specific_condition(self, field: str, description: str) -> Optional[str]:
        """Build a specific condition with user input."""
        print(f"\n🎯 Creating condition for: {description}")
        
        if field == 'customer_tier':
            print("Common customer tiers: premium, enterprise, standard, basic")
            value = input("Enter customer tier: ").strip()
            return f'a customer with tier "{value}"'
            
        elif field == 'sentiment_score':
            print("Sentiment scores range from 0 (very negative) to 1 (very positive)")
            threshold = input("Enter sentiment threshold (e.g., 0.3): ").strip()
            try:
                float(threshold)
                return f"the customer sentiment score is below {threshold}"
            except ValueError:
                print("Invalid number, skipping this condition")
                return None
                
        elif field == 'account_value':
            value = input("Enter minimum account value (e.g., 50000): ").strip()
            try:
                int(value)
                return f"the customer account value is above {value}"
            except ValueError:
                print("Invalid number, skipping this condition")
                return None
                
        elif field == 'data_size':
            size = input("Enter data size threshold (e.g., 100): ").strip()
            try:
                int(size)
                return f"data size is greater than {size}"
            except ValueError:
                print("Invalid number, skipping this condition")
                return None
                
        elif field == 'processing_required':
            return "processing is required"
            
        elif field == 'document_type':
            doc_type = input("Enter document type (e.g., legal, financial, technical): ").strip()
            return f'the document type is "{doc_type}"'
            
        else:
            custom = input(f"Describe the {description} condition: ").strip()
            return custom
            
    def _build_actions_guided(self) -> List[str]:
        """Build actions with guidance."""
        actions = []
        
        print("\n⚡ Available actions:")
        for key, description in self.action_templates.items():
            print(f"{key}. {description}")
        print("9. Custom action")
        print()
        
        while True:
            choice = input("Add an action (1-9) or 'done' to finish: ").strip()
            
            if choice.lower() == 'done':
                break
                
            if choice == '9':
                custom_action = input("Describe your custom action: ").strip()
                framework = self._choose_framework()
                if framework:
                    actions.append(f"{custom_action} using {framework}")
            elif choice in self.action_templates:
                action_desc = self.action_templates[choice]
                action_name = action_desc.split(' - ')[0]
                framework = self._choose_framework()
                if framework:
                    actions.append(f"{action_name} using {framework}")
            else:
                print("Please enter a valid choice (1-9) or 'done'")
                
        return actions
        
    def _choose_framework(self) -> Optional[str]:
        """Let user choose which AI framework to use."""
        print("\nWhich AI system should perform this action?")
        for key, (framework, description) in self.framework_options.items():
            print(f"{key}. {description}")
            
        choice = input("Choose framework (1-6): ").strip()
        if choice in self.framework_options:
            framework, _ = self.framework_options[choice]
            return self.generator.framework_display_names.get(framework, framework)
        else:
            print("Invalid choice, skipping action")
            return None
            
    def _build_freeform(self) -> str:
        """Allow user to write scenario in free form."""
        print("\n✍️  Free-form Scenario Writing")
        print("Write your scenario using natural language.")
        print("Example structure:")
        print()
        print("Scenario: Your business process name")
        print("    Given [condition 1]")
        print("    And [condition 2]")
        print("    When [trigger event]")
        print("    Then [action 1]")
        print("    And [action 2]")
        print()
        print("Enter your scenario (press Ctrl+D when finished):")
        print("-" * 40)
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
            
        scenario = '\n'.join(lines)
        
        # Validate the scenario
        if self._validate_scenario_structure(scenario):
            print("\n✅ Scenario structure looks good!")
        else:
            print("\n⚠️  Scenario might need some adjustments, but we'll proceed.")
            
        return scenario
        
    def _validate_scenario_structure(self, scenario: str) -> bool:
        """Validate basic scenario structure."""
        required_keywords = ['Scenario:', 'Given', 'When', 'Then']
        scenario_lower = scenario.lower()
        
        for keyword in required_keywords:
            if keyword.lower() not in scenario_lower:
                return False
                
        return True
        
    def _assemble_scenario(self, name: str, conditions: List[str], trigger: str, actions: List[str]) -> str:
        """Assemble the final scenario from components."""
        lines = [f"  Scenario: {name}"]
        
        # Add conditions
        for i, condition in enumerate(conditions):
            keyword = "Given" if i == 0 else "And"
            lines.append(f"    {keyword} {condition}")
            
        # Add trigger
        lines.append(f"    When {trigger}")
        
        # Add actions
        for i, action in enumerate(actions):
            keyword = "Then" if i == 0 else "And"
            lines.append(f"    {keyword} {action}")
            
        return '\n'.join(lines)
        
    def _customize_conditions(self, template: str) -> str:
        """Customize conditions in template."""
        print("\n🎯 Customizing Conditions")
        print("Current conditions in template:")
        
        lines = template.split('\n')
        condition_lines = [line for line in lines if 'Given' in line or ('And' in line and any(g in lines[lines.index(line)-1:lines.index(line)-5:-1] for g in ['Given'] if g))]
        
        for i, line in enumerate(condition_lines):
            print(f"{i+1}. {line.strip()}")
            
        print("\nWould you like to:")
        print("1. Add new conditions")
        print("2. Modify existing conditions")
        print("3. Keep as-is")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == '1':
            print("Add new conditions:")
            new_conditions = self._build_conditions_guided()
            # Insert new conditions into template
            # This is a simplified implementation
            for condition in new_conditions:
                template += f"\n    And {condition}"
                
        return template
        
    def _customize_triggers(self, template: str) -> str:
        """Customize triggers in template."""
        print("\n🎯 Customizing Trigger")
        
        lines = template.split('\n')
        when_lines = [line for line in lines if 'When' in line]
        
        if when_lines:
            current_when = when_lines[0].strip()
            print(f"Current trigger: {current_when}")
            
            new_trigger = input("Enter new trigger (or press Enter to keep): ").strip()
            if new_trigger:
                template = template.replace(current_when, f"    When {new_trigger}")
                
        return template
        
    def _customize_actions(self, template: str) -> str:
        """Customize actions in template."""
        print("\n⚡ Customizing Actions")
        print("Add new actions to the scenario:")
        
        new_actions = self._build_actions_guided()
        for action in new_actions:
            template += f"\n    And {action}"
            
        return template


class ScenarioValidator:
    """Validates BDD scenarios for correctness and best practices."""
    
    def __init__(self):
        self.parser = GherkinRuleParser()
        
    def validate_scenario(self, scenario_text: str) -> Dict[str, Any]:
        """Validate a scenario and return validation results."""
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check basic structure
        if not scenario_text.strip():
            results['valid'] = False
            results['errors'].append("Scenario is empty")
            return results
            
        # Check for required keywords
        required_keywords = ['Scenario:', 'Given', 'When', 'Then']
        scenario_lower = scenario_text.lower()
        
        for keyword in required_keywords:
            if keyword.lower() not in scenario_lower:
                results['valid'] = False
                results['errors'].append(f"Missing required keyword: {keyword}")
                
        # Try to parse with GherkinRuleParser
        try:
            rule = self.parser.parse_scenario_text(scenario_text)
            if not rule:
                results['warnings'].append("Could not convert scenario to executable rule")
            else:
                # Validate rule components
                if not rule.conditions:
                    results['suggestions'].append("Consider adding conditions to make the rule more specific")
                    
                if not rule.actions:
                    results['valid'] = False
                    results['errors'].append("Scenario must have at least one action")
                    
                # Check for unknown frameworks
                known_frameworks = ['langchain', 'semantic_kernel', 'mcp', 'temporal', 'fastmcp', 'zep']
                for action in rule.actions:
                    if action.framework not in known_frameworks:
                        results['warnings'].append(f"Unknown framework: {action.framework}")
                        
        except Exception as e:
            results['warnings'].append(f"Parsing warning: {str(e)}")
            
        return results


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Business Logic Scenario Builder')
    parser.add_argument('--build', action='store_true', help='Start interactive scenario builder')
    parser.add_argument('--validate', type=str, help='Validate a scenario file')
    parser.add_argument('--template', choices=['customer', 'document', 'data'], help='Generate a template')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    if args.build:
        builder = InteractiveScenarioBuilder()
        scenario = builder.run_interactive_builder()
        
        if scenario:
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(scenario)
                print(f"\n💾 Scenario saved to: {args.output}")
            else:
                print("\n📋 Final Scenario:")
                print("=" * 40)
                print(scenario)
                
    elif args.validate:
        validator = ScenarioValidator()
        try:
            with open(args.validate, 'r') as f:
                scenario_text = f.read()
                
            results = validator.validate_scenario(scenario_text)
            
            print(f"\n📊 Validation Results for: {args.validate}")
            print("=" * 50)
            
            if results['valid']:
                print("✅ Scenario is valid!")
            else:
                print("❌ Scenario has errors:")
                for error in results['errors']:
                    print(f"   • {error}")
                    
            if results['warnings']:
                print("\n⚠️  Warnings:")
                for warning in results['warnings']:
                    print(f"   • {warning}")
                    
            if results['suggestions']:
                print("\n💡 Suggestions:")
                for suggestion in results['suggestions']:
                    print(f"   • {suggestion}")
                    
        except FileNotFoundError:
            print(f"❌ File not found: {args.validate}")
            
    elif args.template:
        generator = ScenarioTemplateGenerator()
        
        if args.template == 'customer':
            template = generator.generate_customer_service_template()
        elif args.template == 'document':
            template = generator.generate_document_processing_template()
        elif args.template == 'data':
            template = generator.generate_data_pipeline_template()
            
        if args.output:
            with open(args.output, 'w') as f:
                f.write(template)
            print(f"💾 Template saved to: {args.output}")
        else:
            print(template)
            
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
