"""
Temporal Adapter: Integration with Temporal workflow engine.

This module provides the adapter for executing business rules through
Temporal's workflow and activity capabilities.
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
from datetime import timedelta

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class TemporalAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating Temporal with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - Workflow orchestration
    - Activity execution
    - Durable state management
    - Retry and error handling
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("temporal", config)
        self.capabilities = [
            "workflow_orchestration",
            "activity_execution",
            "durable_state",
            "retry_handling",
            "scheduling",
            "saga_patterns"
        ]
        self.client: Optional[Client] = None
        self.worker: Optional[Worker] = None
        self.workflows: Dict[str, Any] = {}
        self.activities: Dict[str, Any] = {}
        self.namespace = config.get("namespace", "default")
        self.task_queue = config.get("task_queue", "business-logic-queue")
        
    async def connect(self) -> None:
        """Connect to Temporal server and initialize worker."""
        try:
            # Connect to Temporal server
            self.client = await Client.connect(
                self.config.get("server_url", "localhost:7233"),
                namespace=self.namespace
            )
            
            # Register built-in workflows and activities
            await self._register_builtin_components()
            
            # Create worker (but don't start it yet)
            self.worker = Worker(
                self.client,
                task_queue=self.task_queue,
                workflows=list(self.workflows.values()),
                activities=list(self.activities.values())
            )
            
            self.is_connected = True
            logger.info("Temporal adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect Temporal adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Temporal server."""
        try:
            if self.worker:
                await self.worker.shutdown()
                
            self.workflows.clear()
            self.activities.clear()
            self.client = None
            self.worker = None
            
            self.is_connected = False
            logger.info("Temporal adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting Temporal adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using Temporal.
        
        Supported actions:
        - start_workflow: Start a new workflow
        - signal_workflow: Send signal to running workflow
        - query_workflow: Query workflow state
        - execute_activity: Execute a single activity
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "start_workflow":
                return await self._start_workflow(params, context)
            elif action_type == "signal_workflow":
                return await self._signal_workflow(params, context)
            elif action_type == "query_workflow":
                return await self._query_workflow(params, context)
            elif action_type == "execute_activity":
                return await self._execute_activity(params, context)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing Temporal action {action_type}: {e}")
            raise
            
    async def _start_workflow(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new Temporal workflow."""
        workflow_name = params.get("workflow_name")
        workflow_id = params.get("workflow_id", f"{workflow_name}_{asyncio.get_event_loop().time()}")
        workflow_params = params.get("parameters", {})
        
        # Get workflow class
        workflow_class = self.workflows.get(workflow_name)
        if not workflow_class:
            raise ValueError(f"Workflow not found: {workflow_name}")
            
        # Merge context and parameters
        merged_params = {**context, **workflow_params}
        
        # Start workflow
        handle = await self.client.start_workflow(
            workflow_class.run,
            merged_params,
            id=workflow_id,
            task_queue=self.task_queue
        )
        
        return {
            "workflow_name": workflow_name,
            "workflow_id": workflow_id,
            "run_id": handle.result_run_id,
            "status": "started",
            "parameters": merged_params
        }
        
    async def _signal_workflow(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send a signal to a running workflow."""
        workflow_id = params.get("workflow_id")
        signal_name = params.get("signal_name")
        signal_data = params.get("signal_data", {})
        
        # Get workflow handle
        handle = self.client.get_workflow_handle(workflow_id)
        
        # Send signal
        await handle.signal(signal_name, signal_data)
        
        return {
            "workflow_id": workflow_id,
            "signal_name": signal_name,
            "signal_data": signal_data,
            "status": "sent"
        }
        
    async def _query_workflow(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Query the state of a workflow."""
        workflow_id = params.get("workflow_id")
        query_name = params.get("query_name", "state")
        
        # Get workflow handle
        handle = self.client.get_workflow_handle(workflow_id)
        
        # Execute query
        result = await handle.query(query_name)
        
        return {
            "workflow_id": workflow_id,
            "query_name": query_name,
            "result": result,
            "status": "completed"
        }
        
    async def _execute_activity(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single activity outside of a workflow."""
        activity_name = params.get("activity_name")
        activity_params = params.get("parameters", {})
        
        # Get activity function
        activity_func = self.activities.get(activity_name)
        if not activity_func:
            raise ValueError(f"Activity not found: {activity_name}")
            
        # Merge context and parameters
        merged_params = {**context, **activity_params}
        
        # Execute activity directly (for testing/development)
        # In production, activities should be executed within workflows
        result = await activity_func(merged_params)
        
        return {
            "activity_name": activity_name,
            "parameters": merged_params,
            "result": result,
            "status": "completed"
        }
        
    async def _register_builtin_components(self) -> None:
        """Register built-in workflows and activities."""
        
        # Business Logic Workflow
        @workflow.defn
        class BusinessLogicWorkflow:
            def __init__(self) -> None:
                self.state = {"status": "initialized"}
                
            @workflow.run
            async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
                self.state["status"] = "running"
                
                # Execute business logic steps
                steps = params.get("steps", [])
                results = []
                
                for step in steps:
                    activity_name = step.get("activity")
                    activity_params = step.get("parameters", {})
                    
                    result = await workflow.execute_activity(
                        activity_name,
                        activity_params,
                        start_to_close_timeout=timedelta(minutes=5)
                    )
                    results.append(result)
                    
                self.state["status"] = "completed"
                self.state["results"] = results
                
                return self.state
                
            @workflow.query
            def state(self) -> Dict[str, Any]:
                return self.state
                
            @workflow.signal
            def update_state(self, update: Dict[str, Any]) -> None:
                self.state.update(update)
                
        self.workflows["business_logic"] = BusinessLogicWorkflow
        
        # Data Processing Workflow
        @workflow.defn
        class DataProcessingWorkflow:
            @workflow.run
            async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
                data = params.get("data", [])
                
                # Process data in batches
                batch_size = params.get("batch_size", 10)
                results = []
                
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    batch_result = await workflow.execute_activity(
                        "process_batch",
                        {"batch": batch},
                        start_to_close_timeout=timedelta(minutes=2)
                    )
                    results.extend(batch_result)
                    
                return {"processed_count": len(results), "results": results}
                
        self.workflows["data_processing"] = DataProcessingWorkflow
        
        # Register activities
        @activity.defn
        async def process_data(params: Dict[str, Any]) -> Dict[str, Any]:
            data = params.get("data", "")
            # Simulate data processing
            processed = f"Processed: {data}"
            return {"result": processed}
            
        self.activities["process_data"] = process_data
        
        @activity.defn
        async def process_batch(params: Dict[str, Any]) -> List[Dict[str, Any]]:
            batch = params.get("batch", [])
            # Simulate batch processing
            results = []
            for item in batch:
                results.append({"original": item, "processed": f"Processed: {item}"})
            return results
            
        self.activities["process_batch"] = process_batch
        
        @activity.defn
        async def validate_data(params: Dict[str, Any]) -> Dict[str, Any]:
            data = params.get("data", "")
            rules = params.get("rules", [])
            # Simulate validation
            is_valid = len(data) > 0 and all(rule in data for rule in rules)
            return {"valid": is_valid, "data": data}
            
        self.activities["validate_data"] = validate_data
        
    def register_workflow(self, name: str, workflow_class: Any) -> None:
        """Register a custom workflow."""
        self.workflows[name] = workflow_class
        logger.info(f"Registered workflow: {name}")
        
    def register_activity(self, name: str, activity_func: Any) -> None:
        """Register a custom activity."""
        self.activities[name] = activity_func
        logger.info(f"Registered activity: {name}")
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Temporal adapter."""
        health_status = await super().health_check()
        
        # Add Temporal-specific metrics
        health_status.update({
            "namespace": self.namespace,
            "task_queue": self.task_queue,
            "workflows_registered": len(self.workflows),
            "activities_registered": len(self.activities),
            "worker_running": self.worker is not None
        })
        
        # Check connection to Temporal server
        if self.client:
            try:
                # Try to describe namespace
                await self.client.service_client.describe_namespace(self.namespace)
                health_status["server_connected"] = True
            except:
                health_status["server_connected"] = False
        else:
            health_status["server_connected"] = False
            
        return health_status