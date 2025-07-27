"""
Simple demonstration of Bizy.

This example shows how to:
1. Set up the orchestrator with multiple framework adapters
2. Define business rules
3. Execute rules across frameworks
4. Handle events and coordination
"""

import asyncio
import logging
from datetime import datetime

from bizy import MetaOrchestrator, BusinessRule
from bizy.core.business_rule import (
    RuleCondition, RuleAction, RuleType, RulePriority
)
from bizy.adapters import (
    setup_default_adapters,
    get_global_registry
)
from bizy.events import EventBus, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_demo_environment():
    """Set up the demo environment with adapters and rules."""
    
    # Initialize event bus
    event_bus = EventBus()
    
    # Subscribe to events for monitoring
    def log_event(event):
        logger.info(f"Event: {event.event_type} - {event.data}")
        
    event_bus.subscribe(EventType.RULE_EXECUTION_STARTED, log_event)
    event_bus.subscribe(EventType.RULE_EXECUTION_COMPLETED, log_event)
    event_bus.subscribe(EventType.RULE_EXECUTION_FAILED, log_event)
    
    # Set up adapters with minimal config
    adapter_config = {
        "langchain": {},
        "semantic_kernel": {},
        "mcp": {"server_url": "http://localhost:8000"},
        "temporal": {"namespace": "default"},
        "fastmcp": {"cache_ttl": 300},
        "zep": {"api_url": "http://localhost:8000"}
    }
    
    # Initialize adapters
    registry = await setup_default_adapters(adapter_config)
    
    # Create meta-orchestrator
    orchestrator = MetaOrchestrator(event_bus)
    
    # Register adapters with orchestrator
    for adapter_name in registry.list_adapters():
        adapter = registry.get_adapter(adapter_name)
        orchestrator.register_adapter(adapter_name, adapter)
        
    return orchestrator, event_bus, registry


async def create_demo_rules():
    """Create demonstration business rules."""
    
    rules = []
    
    # Rule 1: Customer Service Escalation
    escalation_rule = BusinessRule(
        name="customer_escalation",
        rule_type=RuleType.WORKFLOW,
        priority=RulePriority.HIGH,
        conditions=[
            RuleCondition("sentiment_score", "lt", 0.3),
            RuleCondition("customer_tier", "in", ["premium", "enterprise"])
        ],
        actions=[
            RuleAction(
                framework="langchain",
                action="analyze_document",
                parameters={
                    "analysis_type": "sentiment",
                    "content": "Customer complaint text here"
                }
            ),
            RuleAction(
                framework="temporal",
                action="start_workflow",
                parameters={
                    "workflow_name": "customer_escalation",
                    "workflow_id": f"escalation_{datetime.now().timestamp()}"
                }
            ),
            RuleAction(
                framework="zep",
                action="store_memory",
                parameters={
                    "type": "interaction",
                    "content": "Customer escalation triggered"
                }
            )
        ],
        description="Escalate premium customers with negative sentiment"
    )
    rules.append(escalation_rule)
    
    # Rule 2: Data Processing Pipeline
    data_processing_rule = BusinessRule(
        name="data_processing_pipeline",
        rule_type=RuleType.ACTION,
        priority=RulePriority.MEDIUM,
        conditions=[
            RuleCondition("data_size", "gt", 100),
            RuleCondition("processing_required", "eq", True)
        ],
        actions=[
            RuleAction(
                framework="fastmcp",
                action="batch_execute",
                parameters={
                    "executions": [
                        {
                            "tool_name": "batch_processor",
                            "parameters": {
                                "operation": "transform",
                                "data": []
                            }
                        }
                    ],
                    "parallel": True
                }
            ),
            RuleAction(
                framework="mcp",
                action="execute_tool",
                parameters={
                    "tool_name": "data_transformer",
                    "parameters": {
                        "from_format": "json",
                        "to_format": "csv"
                    }
                }
            )
        ],
        description="Process large datasets using optimized tools"
    )
    rules.append(data_processing_rule)
    
    # Rule 3: Knowledge Extraction
    knowledge_rule = BusinessRule(
        name="knowledge_extraction",
        rule_type=RuleType.POLICY,
        priority=RulePriority.LOW,
        conditions=[
            RuleCondition("content_type", "eq", "document"),
            RuleCondition("extract_knowledge", "eq", True)
        ],
        actions=[
            RuleAction(
                framework="semantic_kernel",
                action="run_skill",
                parameters={
                    "skill_name": "Text",
                    "function_name": "ExtractKeywords"
                }
            ),
            RuleAction(
                framework="zep",
                action="extract_facts",
                parameters={
                    "fact_type": "document_facts",
                    "confidence": 0.8
                }
            )
        ],
        description="Extract knowledge from documents"
    )
    rules.append(knowledge_rule)
    
    return rules


async def demonstrate_rule_execution(orchestrator, rules):
    """Demonstrate executing business rules."""
    
    logger.info("\n=== Demonstrating Rule Execution ===\n")
    
    # Test contexts for each rule
    test_contexts = [
        {
            "name": "Premium Customer Complaint",
            "rule": rules[0],  # escalation_rule
            "context": {
                "sentiment_score": 0.2,
                "customer_tier": "premium",
                "customer_id": "CUST-12345",
                "complaint": "Very disappointed with the service"
            }
        },
        {
            "name": "Large Dataset Processing",
            "rule": rules[1],  # data_processing_rule
            "context": {
                "data_size": 500,
                "processing_required": True,
                "data": list(range(500))
            }
        },
        {
            "name": "Document Knowledge Extraction",
            "rule": rules[2],  # knowledge_rule
            "context": {
                "content_type": "document",
                "extract_knowledge": True,
                "content": "This is a sample document about AI orchestration."
            }
        }
    ]
    
    # Execute each test case
    for test_case in test_contexts:
        logger.info(f"\n--- Testing: {test_case['name']} ---")
        
        rule = test_case['rule']
        context = test_case['context']
        
        # Check if rule should execute
        should_execute = rule.should_execute(context)
        logger.info(f"Rule '{rule.name}' should execute: {should_execute}")
        
        if should_execute:
            try:
                # Execute rule
                results = await orchestrator.execute_rule(rule, context)
                
                # Log results
                logger.info(f"Execution results:")
                for adapter_name, result in results.items():
                    if "error" in result:
                        logger.error(f"  {adapter_name}: ERROR - {result['error']}")
                    else:
                        logger.info(f"  {adapter_name}: SUCCESS")
                        logger.debug(f"    Details: {result}")
                        
            except Exception as e:
                logger.error(f"Failed to execute rule: {e}")


async def demonstrate_health_monitoring(registry):
    """Demonstrate health monitoring capabilities."""
    
    logger.info("\n=== Health Monitoring ===\n")
    
    # Perform health check on all adapters
    health_status = await registry.health_check_all()
    
    for adapter_name, status in health_status.items():
        logger.info(f"{adapter_name}:")
        logger.info(f"  Status: {status.get('status', 'unknown')}")
        logger.info(f"  Capabilities: {status.get('capabilities', [])}")
        
        # Log adapter-specific metrics
        if adapter_name == "fastmcp":
            logger.info(f"  Cache hit rate: {status.get('cache_hit_rate', 0):.1f}%")
        elif adapter_name == "temporal":
            logger.info(f"  Workflows: {status.get('workflows_registered', 0)}")
        elif adapter_name == "zep":
            logger.info(f"  Memory sessions: {status.get('memory_sessions', [])}")


async def demonstrate_event_coordination(orchestrator, event_bus):
    """Demonstrate event-based coordination."""
    
    logger.info("\n=== Event Coordination ===\n")
    
    # Create a simple coordination scenario
    coordination_context = {
        "coordination_id": "demo_coord_001",
        "purpose": "Cross-framework data processing"
    }
    
    # Publish coordination start event
    await event_bus.publish(
        EventType.COORDINATION_STARTED,
        {
            "coordination_id": coordination_context["coordination_id"],
            "frameworks": ["langchain", "fastmcp", "zep"],
            "rule_ids": ["data_processing", "memory_storage"]
        }
    )
    
    # Simulate some coordination work
    await asyncio.sleep(0.5)
    
    # Publish coordination complete event
    await event_bus.publish(
        EventType.COORDINATION_COMPLETED,
        {
            "coordination_id": coordination_context["coordination_id"],
            "frameworks": ["langchain", "fastmcp", "zep"],
            "results": {
                "langchain": {"status": "success"},
                "fastmcp": {"status": "success", "items_processed": 100},
                "zep": {"status": "success", "memories_stored": 5}
            },
            "duration_ms": 500
        }
    )
    
    # Show event history
    logger.info("\nEvent History:")
    history = event_bus.get_event_history(limit=10)
    for event in history:
        logger.info(f"  {event.timestamp.strftime('%H:%M:%S')} - {event.event_type}")


async def main():
    """Main demonstration function."""
    
    logger.info("=== Business Logic Orchestrator Demo ===\n")
    
    try:
        # Set up environment
        logger.info("Setting up demo environment...")
        orchestrator, event_bus, registry = await setup_demo_environment()
        
        # Create demo rules
        logger.info("Creating demo business rules...")
        rules = await create_demo_rules()
        
        # Demonstrate rule execution
        await demonstrate_rule_execution(orchestrator, rules)
        
        # Demonstrate health monitoring
        await demonstrate_health_monitoring(registry)
        
        # Demonstrate event coordination
        await demonstrate_event_coordination(orchestrator, event_bus)
        
        logger.info("\n=== Demo Complete ===")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        # Clean up
        logger.info("\nCleaning up...")
        await registry.shutdown_all()


if __name__ == "__main__":
    asyncio.run(main())