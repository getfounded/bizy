"""Reference Implementation of Bizy.

This module provides a complete reference implementation demonstrating
all features and best practices for cross-framework business logic
orchestration.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import orchestrator components
from bizy.core import MetaOrchestrator
from bizy.adapters import (
    LangChainAdapter,
    TemporalAdapter,
    MCPAdapter,
    SemanticKernelAdapter,
    FastMCPAdapter,
    ZepAdapter
)
from bizy.events import EventBus
from bizy.rules import RuleEngine


class ReferenceImplementation:
    """Complete reference implementation of Bizy."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize reference implementation with configuration."""
        self.config_path = config_path or Path("config/reference.yaml")
        self.orchestrator = None
        self.event_bus = None
        self.rule_engine = None
        self.adapters = {}
        
    async def initialize(self) -> None:
        """Initialize all components of the reference implementation."""
        logger.info("Initializing Reference Implementation")
        
        # Initialize event bus
        self.event_bus = EventBus(redis_url="redis://localhost:6379")
        await self.event_bus.connect()
        
        # Initialize rule engine
        self.rule_engine = RuleEngine()
        await self.rule_engine.load_rules("rules/")
        
        # Initialize orchestrator
        self.orchestrator = MetaOrchestrator(
            event_bus=self.event_bus,
            rule_engine=self.rule_engine
        )
        
        # Initialize and register all adapters
        await self._initialize_adapters()
        
        # Set up monitoring
        await self._setup_monitoring()
        
        logger.info("Reference Implementation initialized successfully")
    
    async def _initialize_adapters(self) -> None:
        """Initialize all framework adapters."""
        # LangChain adapter
        langchain_adapter = LangChainAdapter({
            "api_key": os.getenv("LANGCHAIN_API_KEY", ""),
            "model": os.getenv("LANGCHAIN_MODEL", "gpt-4"),
            "temperature": float(os.getenv("LANGCHAIN_TEMPERATURE", "0.7"))
        })
        await langchain_adapter.connect()
        self.orchestrator.register_adapter("langchain", langchain_adapter)
        self.adapters["langchain"] = langchain_adapter
        
        # Temporal adapter
        temporal_adapter = TemporalAdapter({
            "host": os.getenv("TEMPORAL_HOST", "localhost"),
            "port": int(os.getenv("TEMPORAL_PORT", "7233")),
            "namespace": os.getenv("TEMPORAL_NAMESPACE", "default")
        })
        await temporal_adapter.connect()
        self.orchestrator.register_adapter("temporal", temporal_adapter)
        self.adapters["temporal"] = temporal_adapter
        
        # MCP adapter
        mcp_adapter = MCPAdapter({
            "server_url": os.getenv("MCP_SERVER_URL", "http://localhost:8080"),
            "auth_token": os.getenv("MCP_AUTH_TOKEN", "")
        })
        await mcp_adapter.connect()
        self.orchestrator.register_adapter("mcp", mcp_adapter)
        self.adapters["mcp"] = mcp_adapter
        
        # Semantic Kernel adapter
        sk_adapter = SemanticKernelAdapter({
            "api_key": os.getenv("SEMANTIC_KERNEL_API_KEY", ""),
            "skills_directory": os.getenv("SEMANTIC_KERNEL_SKILLS_DIR", "skills/")
        })
        await sk_adapter.connect()
        self.orchestrator.register_adapter("semantic_kernel", sk_adapter)
        self.adapters["semantic_kernel"] = sk_adapter
        
        # FastMCP adapter
        fastmcp_adapter = FastMCPAdapter({
            "server_name": "reference-server",
            "tools_directory": "tools/"
        })
        await fastmcp_adapter.connect()
        self.orchestrator.register_adapter("fastmcp", fastmcp_adapter)
        self.adapters["fastmcp"] = fastmcp_adapter
        
        # Zep adapter
        zep_adapter = ZepAdapter({
            "api_url": os.getenv("ZEP_API_URL", "http://localhost:8000"),
            "api_key": os.getenv("ZEP_API_KEY", "")
        })
        await zep_adapter.connect()
        self.orchestrator.register_adapter("zep", zep_adapter)
        self.adapters["zep"] = zep_adapter
        
        logger.info("All adapters initialized and registered")
    
    async def _setup_monitoring(self) -> None:
        """Set up monitoring and observability."""
        # Metrics collection
        self.orchestrator.enable_metrics({
            "endpoint": "http://localhost:9090/metrics",
            "interval": 10
        })
        
        # Distributed tracing
        self.orchestrator.enable_tracing({
            "endpoint": "http://localhost:16686",
            "service_name": "business-logic-orchestrator"
        })
        
        # Health checks
        self.orchestrator.enable_health_checks({
            "port": 8888,
            "path": "/health"
        })
        
        logger.info("Monitoring and observability configured")
    
    async def demonstrate_customer_service_workflow(self) -> Dict[str, Any]:
        """Demonstrate complete customer service workflow."""
        logger.info("Starting Customer Service Workflow Demonstration")
        
        # Sample customer interaction
        customer_message = "I'm very frustrated with my recent order!"
        customer_id = "CUST-12345"
        
        # Step 1: Analyze sentiment with LangChain
        sentiment_result = await self.orchestrator.execute_action(
            framework="langchain",
            action="analyze_sentiment",
            params={
                "text": customer_message,
                "include_emotions": True
            }
        )
        logger.info(f"Sentiment Analysis: {sentiment_result}")
        
        # Step 2: Fetch customer data with MCP
        customer_data = await self.orchestrator.execute_action(
            framework="mcp",
            action="get_customer_profile",
            params={"customer_id": customer_id}
        )
        logger.info(f"Customer Data: {customer_data}")
        
        # Step 3: Store interaction in Zep memory
        memory_result = await self.orchestrator.execute_action(
            framework="zep",
            action="store_interaction",
            params={
                "user_id": customer_id,
                "message": customer_message,
                "metadata": sentiment_result
            }
        )
        
        # Step 4: Evaluate business rules
        rule_context = {
            "customer": customer_data,
            "sentiment": sentiment_result,
            "message": customer_message
        }
        
        rule_decision = await self.orchestrator.evaluate_rules(
            rule_set="customer_service",
            context=rule_context
        )
        logger.info(f"Rule Decision: {rule_decision}")
        
        # Step 5: Execute decision-based actions
        if rule_decision["decision"] == "escalate":
            # Start Temporal workflow for escalation
            workflow_result = await self.orchestrator.execute_action(
                framework="temporal",
                action="start_escalation_workflow",
                params={
                    "customer_id": customer_id,
                    "priority": "high",
                    "context": rule_context
                }
            )
            
            # Generate response with Semantic Kernel
            response = await self.orchestrator.execute_action(
                framework="semantic_kernel",
                action="generate_escalation_response",
                params={
                    "customer_name": customer_data.get("name"),
                    "issue": sentiment_result.get("main_concern"),
                    "ticket_id": workflow_result.get("workflow_id")
                }
            )
        else:
            # Generate standard response
            response = await self.orchestrator.execute_action(
                framework="semantic_kernel",
                action="generate_response",
                params={
                    "context": rule_context,
                    "tone": "empathetic"
                }
            )
        
        # Step 6: Log with FastMCP
        await self.orchestrator.execute_action(
            framework="fastmcp",
            action="log_interaction",
            params={
                "interaction_id": memory_result.get("session_id"),
                "customer_id": customer_id,
                "resolution": response
            }
        )
        
        return {
            "customer_message": customer_message,
            "sentiment": sentiment_result,
            "decision": rule_decision["decision"],
            "response": response,
            "workflow_id": workflow_result.get("workflow_id") if rule_decision["decision"] == "escalate" else None
        }
    
    async def demonstrate_document_processing_pipeline(self) -> Dict[str, Any]:
        """Demonstrate document processing across frameworks."""
        logger.info("Starting Document Processing Pipeline Demonstration")
        
        document_path = "samples/contract.pdf"
        
        # Parallel processing with multiple frameworks
        tasks = [
            self.orchestrator.execute_action(
                framework="mcp",
                action="extract_text",
                params={"document_path": document_path}
            ),
            self.orchestrator.execute_action(
                framework="fastmcp",
                action="extract_metadata",
                params={"file_path": document_path}
            )
        ]
        
        extraction_results = await asyncio.gather(*tasks)
        text_content = extraction_results[0]["text"]
        metadata = extraction_results[1]["metadata"]
        
        # Analyze with LangChain
        analysis = await self.orchestrator.execute_action(
            framework="langchain",
            action="analyze_document",
            params={
                "text": text_content,
                "analysis_type": "contract_review"
            }
        )
        
        # Store in Zep for future reference
        storage_result = await self.orchestrator.execute_action(
            framework="zep",
            action="store_document",
            params={
                "document_id": metadata.get("hash"),
                "content": text_content,
                "analysis": analysis,
                "metadata": metadata
            }
        )
        
        # Create workflow if action required
        if analysis.get("requires_review", False):
            workflow = await self.orchestrator.execute_action(
                framework="temporal",
                action="start_document_review",
                params={
                    "document_id": storage_result["document_id"],
                    "issues": analysis.get("issues", []),
                    "deadline": analysis.get("suggested_deadline")
                }
            )
        
        return {
            "document": document_path,
            "metadata": metadata,
            "analysis": analysis,
            "storage_id": storage_result["document_id"],
            "review_workflow": workflow if analysis.get("requires_review") else None
        }
    
    async def demonstrate_cross_framework_coordination(self) -> Dict[str, Any]:
        """Demonstrate complex cross-framework coordination."""
        logger.info("Starting Cross-Framework Coordination Demonstration")
        
        # Define coordination sequence
        coordination_plan = [
            {
                "framework": "langchain",
                "action": "generate_plan",
                "params": {"objective": "Process customer feedback batch"}
            },
            {
                "framework": "temporal",
                "action": "create_batch_workflow",
                "params": {"plan": "{previous.result}"}
            },
            {
                "framework": "mcp",
                "action": "fetch_feedback_data",
                "params": {"batch_size": 100}
            },
            {
                "framework": "semantic_kernel",
                "action": "analyze_feedback_batch",
                "params": {"data": "{previous.result}"}
            },
            {
                "framework": "zep",
                "action": "update_customer_profiles",
                "params": {"insights": "{previous.result}"}
            },
            {
                "framework": "fastmcp",
                "action": "generate_report",
                "params": {"all_results": "{context}"}
            }
        ]
        
        # Execute coordination
        result = await self.orchestrator.coordinate_frameworks(
            plan=coordination_plan,
            execution_mode="sequential",
            error_handling="continue_on_error"
        )
        
        return result
    
    async def demonstrate_business_rule_patterns(self) -> None:
        """Demonstrate various business rule patterns."""
        logger.info("Demonstrating Business Rule Patterns")
        
        # Pattern 1: Simple condition-action
        simple_rule = {
            "name": "high_value_alert",
            "conditions": ["transaction.amount > 10000"],
            "actions": [
                {
                    "framework": "fastmcp",
                    "action": "send_alert",
                    "params": {"channel": "finance_team"}
                }
            ]
        }
        
        # Pattern 2: Complex multi-condition
        complex_rule = {
            "name": "fraud_detection",
            "conditions": [
                "transaction.amount > customer.average_transaction * 5",
                "transaction.location != customer.home_location",
                "transaction.time not in customer.typical_hours"
            ],
            "operator": "AND",
            "actions": [
                {
                    "framework": "temporal",
                    "action": "start_fraud_investigation",
                    "priority": 1
                },
                {
                    "framework": "fastmcp",
                    "action": "block_transaction",
                    "priority": 2
                }
            ]
        }
        
        # Pattern 3: ML-enhanced rules
        ml_rule = {
            "name": "customer_churn_prevention",
            "conditions": [
                {
                    "framework": "langchain",
                    "action": "predict_churn_probability",
                    "threshold": 0.7
                }
            ],
            "actions": [
                {
                    "framework": "semantic_kernel",
                    "action": "generate_retention_offer"
                },
                {
                    "framework": "mcp",
                    "action": "schedule_followup"
                }
            ]
        }
        
        # Register and demonstrate rules
        for rule in [simple_rule, complex_rule, ml_rule]:
            self.rule_engine.register_rule(rule)
            logger.info(f"Registered rule: {rule['name']}")
    
    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmarks across all frameworks."""
        logger.info("Running Performance Benchmarks")
        
        benchmarks = {}
        iterations = 100
        
        # Benchmark each framework
        for framework_name, adapter in self.adapters.items():
            start_time = asyncio.get_event_loop().time()
            
            # Run simple operations
            for i in range(iterations):
                await self.orchestrator.execute_action(
                    framework=framework_name,
                    action="health_check",
                    params={}
                )
            
            end_time = asyncio.get_event_loop().time()
            avg_time = (end_time - start_time) / iterations * 1000  # ms
            
            benchmarks[framework_name] = {
                "average_latency_ms": avg_time,
                "operations_per_second": iterations / (end_time - start_time)
            }
        
        # Benchmark rule evaluation
        rule_start = asyncio.get_event_loop().time()
        for i in range(iterations):
            await self.orchestrator.evaluate_rules(
                rule_set="performance_test",
                context={"value": i}
            )
        rule_end = asyncio.get_event_loop().time()
        
        benchmarks["rule_evaluation"] = {
            "average_latency_ms": (rule_end - rule_start) / iterations * 1000,
            "evaluations_per_second": iterations / (rule_end - rule_start)
        }
        
        logger.info(f"Benchmarks: {benchmarks}")
        return benchmarks
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all components."""
        logger.info("Shutting down Reference Implementation")
        
        # Disconnect all adapters
        for name, adapter in self.adapters.items():
            await adapter.disconnect()
            logger.info(f"Disconnected {name} adapter")
        
        # Shutdown event bus
        await self.event_bus.disconnect()
        
        # Save rule engine state
        await self.rule_engine.save_state()
        
        logger.info("Reference Implementation shutdown complete")


async def main():
    """Run the reference implementation demonstrations."""
    # Initialize
    implementation = ReferenceImplementation()
    await implementation.initialize()
    
    try:
        # Run demonstrations
        print("\n=== Customer Service Workflow ===")
        cs_result = await implementation.demonstrate_customer_service_workflow()
        print(f"Result: {cs_result}")
        
        print("\n=== Document Processing Pipeline ===")
        doc_result = await implementation.demonstrate_document_processing_pipeline()
        print(f"Result: {doc_result}")
        
        print("\n=== Cross-Framework Coordination ===")
        coord_result = await implementation.demonstrate_cross_framework_coordination()
        print(f"Result: {coord_result}")
        
        print("\n=== Business Rule Patterns ===")
        await implementation.demonstrate_business_rule_patterns()
        
        print("\n=== Performance Benchmarks ===")
        benchmarks = await implementation.run_performance_benchmark()
        print(f"Benchmarks: {benchmarks}")
        
    finally:
        # Cleanup
        await implementation.shutdown()


if __name__ == "__main__":
    asyncio.run(main())