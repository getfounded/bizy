#!/usr/bin/env python3
"""
BDD Integration Demo Script for Business Logic Orchestrator

This script demonstrates how the BDD integration works with the existing
business logic orchestration system, showing natural language business
rule definition and execution.
"""

import asyncio
import json
from pathlib import Path
import sys
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from business_logic_orchestrator.core.meta_orchestrator import MetaOrchestrator
from business_logic_orchestrator.core.business_rule import (
    BusinessRule, RuleCondition, RuleAction, RuleType, RulePriority
)
from business_logic_orchestrator.bdd import (
    GherkinRuleParser, BDDScenarioExecutor, BDDDocumentationGenerator
)
from business_logic_orchestrator.bdd.gherkin_parser import ScenarioTemplateGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_existing_rule_to_gherkin():
    """Demonstrate converting existing BusinessRule objects to natural language."""
    print("🔄 Demo: Converting Existing Business Rules to BDD Scenarios")
    print("=" * 60)
    
    # Use the existing customer escalation rule from the demo
    rule = BusinessRule(
        name="Premium customer escalation workflow",
        rule_type=RuleType.WORKFLOW,
        priority=RulePriority.HIGH,
        conditions=[
            RuleCondition("customer.tier", "eq", "premium"),
            RuleCondition("sentiment_score", "lt", 0.3),
            RuleCondition("customer.account_value", "gt", 10000)
        ],
        actions=[
            RuleAction("langchain", "analyze_sentiment", {"analysis_type": "detailed"}),
            RuleAction("temporal", "start_escalation_workflow", {"priority": "high"}),
            RuleAction("mcp", "notify_account_manager", {"urgency": "immediate"}),
            RuleAction("zep", "update_customer_context", {"interaction_type": "escalation"})
        ],
        description="Escalate premium customers with negative sentiment and high account value"
    )
    
    # Convert to natural language BDD scenario
    generator = BDDDocumentationGenerator()
    scenario_text = generator.generate_scenario(rule)
    
    print("✅ Existing BusinessRule converted to BDD scenario:")
    print(scenario_text)
    print()
    
    # Generate business stakeholder summary
    stakeholder_summary = generator.generate_stakeholder_summary([rule])
    print("📊 Business Stakeholder Summary:")
    print("=" * 40)
    print(stakeholder_summary[:500] + "...")  # Show first 500 chars
    
    return rule, scenario_text


async def demo_gherkin_to_rule_conversion():
    """Demonstrate converting natural language scenarios to BusinessRule objects."""
    print("\n🎭 Demo: Converting Natural Language to Executable Rules")
    print("=" * 60)
    
    # Create a natural language scenario
    scenario_text = '''
Scenario: High-value customer data processing workflow
    Given a customer with tier "enterprise"
    And the customer account value is above 100000
    And data size is greater than 500
    When the data pipeline is triggered
    Then analyze customer data using LangChain
    And coordinate processing agents via Semantic Kernel
    And start data workflow via Temporal
    And batch process data via FastMCP
    And store analysis context in Zep memory
    '''
    
    print("📝 Natural Language Scenario:")
    print(scenario_text)
    
    # Parse into BusinessRule
    parser = GherkinRuleParser()
    rule = parser.parse_scenario_text(scenario_text)
    
    if rule:
        print("\n✅ Converted to BusinessRule:")
        print(f"   Name: {rule.name}")
        print(f"   Type: {rule.rule_type.value}")
        print(f"   Priority: {rule.priority.name}")
        print(f"   Conditions: {len(rule.conditions)}")
        for condition in rule.conditions:
            print(f"     - {condition.field} {condition.operator} {condition.value}")
        print(f"   Actions: {len(rule.actions)}")
        for action in rule.actions:
            print(f"     - {action.framework}: {action.action}")
    else:
        print("❌ Failed to parse scenario")
        
    return rule


async def demo_bdd_execution_with_orchestrator():
    """Demonstrate executing BDD scenarios through the existing orchestrator."""
    print("\n⚡ Demo: Executing BDD Scenarios with Orchestrator")
    print("=" * 60)
    
    # Create orchestrator (same as existing demo)
    orchestrator = MetaOrchestrator()
    bdd_executor = BDDScenarioExecutor(orchestrator)
    
    # Create a sample business context
    context = {
        "customer": {
            "tier": "premium",
            "account_value": 75000,
            "sentiment_score": 0.25
        },
        "interaction": {
            "type": "support_ticket",
            "category": "billing",
            "priority": "urgent"
        }
    }
    
    # Create a rule that matches our context
    rule = BusinessRule(
        name="Premium customer support escalation",
        conditions=[
            RuleCondition("customer.tier", "eq", "premium"),
            RuleCondition("customer.sentiment_score", "lt", 0.3)
        ],
        actions=[
            RuleAction("langchain", "analyze_sentiment", {"deep_analysis": True}),
            RuleAction("temporal", "start_escalation_workflow", {"priority": "urgent"}),
            RuleAction("mcp", "notify_account_manager", {"method": "immediate"})
        ]
    )
    
    print(f"📋 Executing rule: {rule.name}")
    print(f"📊 Context: Customer tier={context['customer']['tier']}, Sentiment={context['customer']['sentiment_score']}")
    
    # Execute through BDD executor
    result = await bdd_executor.execute_business_rule(rule, context)
    
    print(f"\n🎯 Execution Result:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Skipped: {result.get('skipped', False)}")
    if result.get('skipped'):
        print(f"   Reason: {result.get('reason', 'Unknown')}")
    else:
        print(f"   Conditions Evaluated: {result.get('conditions_evaluated', 0)}")
        print(f"   Actions Executed: {result.get('actions_executed', 0)}")
        print(f"   Frameworks Involved: {result.get('frameworks_involved', [])}")
    
    return result


async def demo_business_process_templates():
    """Demonstrate business process templates for stakeholders."""
    print("\n📋 Demo: Business Process Templates")
    print("=" * 60)
    
    # Generate templates for common business scenarios
    templates = {
        "Customer Service": ScenarioTemplateGenerator.generate_customer_service_template(),
        "Document Processing": ScenarioTemplateGenerator.generate_document_processing_template(),
        "Data Pipeline": ScenarioTemplateGenerator.generate_data_pipeline_template()
    }
    
    for template_name, template_content in templates.items():
        print(f"\n📄 {template_name} Template:")
        print("-" * 40)
        # Show first few lines of each template
        lines = template_content.split('\n')[:8]
        for line in lines:
            print(line)
        print("    ...")
        
    print(f"\n✅ Generated {len(templates)} business process templates")
    print("💡 Stakeholders can customize these templates for their specific needs")
    
    return templates


async def demo_feature_file_execution():
    """Demonstrate executing a complete feature file."""
    print("\n📁 Demo: Feature File Execution")
    print("=" * 60)
    
    # Check if feature file exists
    feature_file = Path("features/cross_framework_orchestration.feature")
    
    if feature_file.exists():
        print(f"📂 Found feature file: {feature_file.name}")
        
        # Parse the feature file
        parser = GherkinRuleParser()
        try:
            rules = parser.parse_feature_file(feature_file)
            print(f"✅ Parsed {len(rules)} business rules from feature file")
            
            for i, rule in enumerate(rules[:3], 1):  # Show first 3 rules
                print(f"   {i}. {rule.name}")
                print(f"      - {len(rule.conditions)} conditions")
                print(f"      - {len(rule.actions)} actions")
                print(f"      - Priority: {rule.priority.name}")
                
        except Exception as e:
            print(f"❌ Error parsing feature file: {e}")
            rules = []
    else:
        print(f"📂 Feature file not found: {feature_file}")
        print("💡 Run this demo from the project root directory")
        rules = []
        
    return rules


async def demo_living_documentation():
    """Demonstrate generating living documentation from business rules."""
    print("\n📚 Demo: Living Documentation Generation")
    print("=" * 60)
    
    # Create a set of business rules representing different scenarios
    rules = [
        BusinessRule(
            name="Premium customer escalation",
            rule_type=RuleType.WORKFLOW,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition("customer.tier", "eq", "premium"),
                RuleCondition("sentiment_score", "lt", 0.3)
            ],
            actions=[
                RuleAction("temporal", "start_escalation_workflow", {}),
                RuleAction("mcp", "notify_account_manager", {})
            ]
        ),
        BusinessRule(
            name="Large dataset processing",
            rule_type=RuleType.ACTION,
            priority=RulePriority.MEDIUM,
            conditions=[
                RuleCondition("data_size", "gt", 1000),
                RuleCondition("processing_required", "eq", True)
            ],
            actions=[
                RuleAction("fastmcp", "batch_process", {}),
                RuleAction("zep", "store_context", {})
            ]
        ),
        BusinessRule(
            name="Document knowledge extraction",
            rule_type=RuleType.POLICY,
            priority=RulePriority.LOW,
            conditions=[
                RuleCondition("document_type", "eq", "legal"),
                RuleCondition("extract_knowledge", "eq", True)
            ],
            actions=[
                RuleAction("langchain", "extract_entities", {}),
                RuleAction("semantic_kernel", "analyze_content", {})
            ]
        )
    ]
    
    # Generate documentation
    generator = BDDDocumentationGenerator()
    
    # Business process documentation
    process_doc = generator.generate_business_process_documentation(
        rules, 
        "AI Business Logic Automation"
    )
    
    # Stakeholder summary
    stakeholder_summary = generator.generate_stakeholder_summary(rules)
    
    # Feature file
    feature_file = generator.generate_feature_file(
        rules,
        "AI Business Process Automation",
        "Automated business logic that coordinates AI systems for enterprise workflows"
    )
    
    print("📄 Generated Documentation Types:")
    print(f"   1. Business Process Documentation ({len(process_doc)} characters)")
    print(f"   2. Stakeholder Summary ({len(stakeholder_summary)} characters)")
    print(f"   3. Feature File ({len(feature_file)} characters)")
    
    print("\n📋 Sample Feature File Content:")
    print("-" * 40)
    feature_lines = feature_file.split('\n')[:15]
    for line in feature_lines:
        print(line)
    print("    ...")
    
    return {
        'process_doc': process_doc,
        'stakeholder_summary': stakeholder_summary,
        'feature_file': feature_file
    }


async def demo_community_contribution_example():
    """Demonstrate how this creates shareable patterns for the community."""
    print("\n🌐 Demo: Community Contribution Patterns")
    print("=" * 60)
    
    print("🎯 Value for Behave Community:")
    print("   • Natural language AI system testing")
    print("   • Business stakeholder involvement in test creation")
    print("   • Cross-framework coordination testing patterns")
    print("   • Living documentation that stays current")
    
    print("\n🎯 Value for Cucumber Community:")
    print("   • AI testing patterns across multiple languages")
    print("   • Enterprise business process automation testing")
    print("   • Framework-agnostic business logic patterns")
    print("   • Real-world complex system coordination examples")
    
    print("\n🎯 Value for AI Framework Communities:")
    print("   • Standardized testing approaches for framework integration")
    print("   • Business-friendly validation of AI system behavior")
    print("   • Cross-framework coordination best practices")
    print("   • Reduced barrier to entry for business stakeholders")
    
    # Create example contribution package structure
    contribution_structure = {
        "behave-ai-orchestration": [
            "setup.py",
            "behave_ai_orchestration/",
            "  __init__.py",
            "  steps/",
            "    ai_frameworks.py",
            "    business_logic.py",
            "    coordination.py",
            "  templates/",
            "    customer_service.feature",
            "    document_processing.feature",
            "  examples/",
            "    README.md"
        ],
        "cucumber-ai-patterns": [
            "package.json",
            "features/",
            "  step_definitions/",
            "    ai_frameworks.js",
            "    business_logic.js",
            "support/",
            "  world.js",
            "templates/",
            "  enterprise_workflows.feature"
        ]
    }
    
    print("\n📦 Example Community Contribution Packages:")
    for package_name, structure in contribution_structure.items():
        print(f"\n{package_name}/")
        for item in structure:
            print(f"  {item}")
    
    print("\n✨ Innovation Highlights:")
    print("   🆕 First business-stakeholder-accessible AI testing")
    print("   🆕 First comprehensive cross-framework BDD integration")
    print("   🆕 First executable business process documentation for AI")
    print("   🆕 First community ecosystem for AI business logic patterns")


async def main():
    """Main demonstration function."""
    print("🚀 Business Logic Orchestrator - BDD Integration Demo")
    print("=" * 70)
    print("Demonstrating integration with existing business logic orchestration system")
    print()
    
    try:
        # Run all demonstrations
        existing_rule, scenario_text = await demo_existing_rule_to_gherkin()
        new_rule = await demo_gherkin_to_rule_conversion()
        execution_result = await demo_bdd_execution_with_orchestrator()
        templates = await demo_business_process_templates()
        feature_rules = await demo_feature_file_execution()
        documentation = await demo_living_documentation()
        await demo_community_contribution_example()
        
        # Summary
        print("\n🎉 Demo Results Summary:")
        print("=" * 40)
        print(f"   ✅ Existing rule → BDD conversion: Success")
        print(f"   ✅ Natural language → Rule parsing: {'Success' if new_rule else 'Failed'}")
        print(f"   ✅ BDD scenario execution: {'Success' if execution_result.get('success') else 'Failed'}")
        print(f"   ✅ Business process templates: {len(templates)} generated")
        print(f"   ✅ Feature file parsing: {len(feature_rules)} rules extracted")
        print(f"   ✅ Living documentation: {len(documentation)} formats generated")
        
        print("\n🎯 Key Achievements:")
        print("   • Business stakeholders can write AI system rules in natural language")
        print("   • Existing BusinessRule objects auto-convert to stakeholder-friendly docs")
        print("   • BDD scenarios execute through existing MetaOrchestrator")
        print("   • Living documentation stays current with implementation")
        print("   • Community contribution packages ready for ecosystem")
        
        print("\n🚀 Next Steps:")
        print("   1. Run BDD tests: `poetry run behave features/`")
        print("   2. Generate business documentation: `poetry run python -c 'import asyncio; from business_logic_orchestrator.bdd import *; ...'`")
        print("   3. Create custom business scenarios using templates")
        print("   4. Contribute patterns to Behave/Cucumber communities")
        
        print("\n💡 Business Impact:")
        print("   • 🏢 Business stakeholders become AI system contributors")
        print("   • 📚 Executable specifications eliminate miscommunication")
        print("   • 🔄 Living documentation always reflects current behavior")
        print("   • 🌐 Community patterns accelerate industry adoption")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
