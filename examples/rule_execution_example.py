"""
Example demonstrating Business Rule Definition Language usage.

This example shows how to:
1. Parse YAML rule definitions
2. Validate rules
3. Compile rules for optimization
4. Execute rules with the orchestrator
"""

import asyncio
import logging
from pathlib import Path

from business_logic_orchestrator.rules import (
    RuleParser, RuleValidator, RuleCompiler, RuleExecutor
)
from business_logic_orchestrator.core import MetaOrchestrator
from business_logic_orchestrator.events import EventBus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate rule parsing, validation, compilation, and execution."""
    
    # Initialize components
    event_bus = EventBus()
    orchestrator = MetaOrchestrator(event_bus)
    
    # Initialize rule components
    parser = RuleParser()
    validator = RuleValidator(orchestrator)
    compiler = RuleCompiler()
    executor = RuleExecutor(orchestrator, event_bus)
    
    # Load example rules
    rules_dir = Path("examples/rules")
    rule_files = [
        "customer_escalation.yaml",
        "fraud_detection.yaml",
        "inventory_optimization.yaml"
    ]
    
    for rule_file in rule_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing rule: {rule_file}")
        logger.info(f"{'='*60}")
        
        # Parse rule
        try:
            rule = parser.parse_file(rules_dir / rule_file)
            logger.info(f"✓ Successfully parsed rule: {rule.name}")
            logger.info(f"  - ID: {rule.id}")
            logger.info(f"  - Priority: {rule.priority}")
            logger.info(f"  - Conditions: {len(rule.conditions)}")
            logger.info(f"  - Actions: {len(rule.actions)}")
            
        except Exception as e:
            logger.error(f"✗ Failed to parse rule: {e}")
            continue
            
        # Validate rule
        validation_result = validator.validate(rule)
        
        if validation_result.valid:
            logger.info("✓ Rule validation passed")
        else:
            logger.error("✗ Rule validation failed:")
            for error in validation_result.errors:
                logger.error(f"  - {error}")
                
        if validation_result.warnings:
            logger.warning("⚠ Validation warnings:")
            for warning in validation_result.warnings:
                logger.warning(f"  - {warning}")
                
        if validation_result.suggestions:
            logger.info("💡 Suggestions:")
            for suggestion in validation_result.suggestions:
                logger.info(f"  - {suggestion}")
                
        # Compile rule
        compilation_result = compiler.compile(rule, optimization_level=2)
        
        if compilation_result.success:
            logger.info("✓ Rule compilation successful")
            compiled_rule = compilation_result.compiled_rule
            
            # Show execution plan
            logger.info("📋 Execution plan:")
            for i, stage in enumerate(compiled_rule.execution_plan):
                actions = [a.action for a in stage]
                logger.info(f"  Stage {i+1}: {', '.join(actions)} (parallel)")
                
            # Show optimization stats
            if compilation_result.optimization_stats:
                logger.info("📊 Optimization statistics:")
                for key, value in compilation_result.optimization_stats.items():
                    logger.info(f"  - {key}: {value}")
                    
        else:
            logger.error("✗ Rule compilation failed:")
            for error in compilation_result.errors:
                logger.error(f"  - {error}")
                
        # Example: Execute rule with sample context
        if rule.id == "customer_escalation":
            logger.info("\n🚀 Executing customer escalation rule with sample data...")
            
            sample_context = {
                "customer_id": "CUST-12345",
                "customer_tier": "premium",
                "sentiment_score": 0.25,  # Negative sentiment
                "interaction_count": 3,
                "customer_context": {
                    "name": "John Doe",
                    "account_value": 50000,
                    "tenure_years": 5
                }
            }
            
            try:
                # Note: This would actually execute if adapters were connected
                result = await executor.execute(rule, sample_context)
                
                logger.info(f"✓ Execution completed: {'Success' if result.success else 'Failed'}")
                logger.info(f"  - Duration: {result.duration:.2f}s")
                logger.info(f"  - Conditions evaluated: {len(result.conditions_evaluated)}")
                logger.info(f"  - Actions executed: {len(result.actions_executed)}")
                
                if result.errors:
                    logger.error("  - Errors:")
                    for error in result.errors:
                        logger.error(f"    • {error}")
                        
            except Exception as e:
                logger.error(f"✗ Execution failed: {e}")
                
    # Example: Convert rule back to YAML
    logger.info(f"\n{'='*60}")
    logger.info("Converting rule back to YAML")
    logger.info(f"{'='*60}")
    
    if 'rule' in locals():
        yaml_output = parser.to_yaml(rule)
        logger.info("Generated YAML:")
        print(yaml_output)
        
    # Example: Compose multiple rules
    logger.info(f"\n{'='*60}")
    logger.info("Rule composition example")
    logger.info(f"{'='*60}")
    
    if len(rule_files) >= 2:
        # Parse two rules for composition
        rule1 = parser.parse_file(rules_dir / rule_files[0])
        rule2 = parser.parse_file(rules_dir / rule_files[1])
        
        # Compose rules
        composed_rule = compiler.compose_rules(rule1, rule2, composition_type="extend")
        logger.info(f"✓ Composed rule created: {composed_rule.id}")
        logger.info(f"  - Total conditions: {len(composed_rule.conditions)}")
        logger.info(f"  - Total actions: {len(composed_rule.actions)}")


if __name__ == "__main__":
    asyncio.run(main())