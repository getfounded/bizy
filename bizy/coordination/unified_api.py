"""
Unified API: Single interface for business rule execution across frameworks.

This module provides a unified API that abstracts away framework-specific
details and provides a consistent interface for business logic execution.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime

from ..core.meta_orchestrator import MetaOrchestrator
from ..core.business_rule import BusinessRule
from ..events import EventBus
from .protocol_translator import ProtocolTranslator, MessageFormat, ProtocolType

logger = logging.getLogger(__name__)


class APIEndpoint(str, Enum):
    """Available API endpoints."""
    EXECUTE_RULE = "/api/v1/rules/execute"
    CREATE_RULE = "/api/v1/rules/create"
    LIST_RULES = "/api/v1/rules/list"
    DELETE_RULE = "/api/v1/rules/delete"
    
    FRAMEWORK_STATUS = "/api/v1/frameworks/status"
    FRAMEWORK_CAPABILITIES = "/api/v1/frameworks/capabilities"
    
    WORKFLOW_START = "/api/v1/workflows/start"
    WORKFLOW_STATUS = "/api/v1/workflows/status"
    
    HEALTH_CHECK = "/api/v1/health"
    METRICS = "/api/v1/metrics"


@dataclass
class APIRequest:
    """Standard API request format."""
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    query_params: Dict[str, str]
    auth_token: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.request_id:
            import uuid
            self.request_id = str(uuid.uuid4())


@dataclass
class APIResponse:
    """Standard API response format."""
    status_code: int
    body: Dict[str, Any]
    headers: Dict[str, str]
    request_id: str
    timestamp: datetime = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class UnifiedAPI:
    """
    Provides a unified API for business rule execution across all frameworks.
    
    Features:
    - Single endpoint for rule execution
    - Automatic framework selection
    - Protocol translation
    - Error standardization
    - Request/response validation
    """
    
    def __init__(
        self,
        orchestrator: MetaOrchestrator,
        event_bus: EventBus,
        protocol_translator: Optional[ProtocolTranslator] = None
    ):
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.protocol_translator = protocol_translator or ProtocolTranslator()
        self.endpoints: Dict[str, Callable] = {}
        self._register_endpoints()
        
    def _register_endpoints(self):
        """Register API endpoint handlers."""
        self.endpoints = {
            APIEndpoint.EXECUTE_RULE: self._handle_execute_rule,
            APIEndpoint.CREATE_RULE: self._handle_create_rule,
            APIEndpoint.LIST_RULES: self._handle_list_rules,
            APIEndpoint.DELETE_RULE: self._handle_delete_rule,
            APIEndpoint.FRAMEWORK_STATUS: self._handle_framework_status,
            APIEndpoint.FRAMEWORK_CAPABILITIES: self._handle_framework_capabilities,
            APIEndpoint.WORKFLOW_START: self._handle_workflow_start,
            APIEndpoint.WORKFLOW_STATUS: self._handle_workflow_status,
            APIEndpoint.HEALTH_CHECK: self._handle_health_check,
            APIEndpoint.METRICS: self._handle_metrics
        }
        
    async def handle_request(self, request: APIRequest) -> APIResponse:
        """
        Handle incoming API request.
        
        Args:
            request: API request object
            
        Returns:
            API response object
        """
        try:
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                return APIResponse(
                    status_code=400,
                    body={"error": validation_error},
                    headers={"Content-Type": "application/json"},
                    request_id=request.request_id,
                    error=validation_error
                )
                
            # Get endpoint handler
            handler = self.endpoints.get(request.endpoint)
            if not handler:
                return APIResponse(
                    status_code=404,
                    body={"error": f"Unknown endpoint: {request.endpoint}"},
                    headers={"Content-Type": "application/json"},
                    request_id=request.request_id,
                    error="Endpoint not found"
                )
                
            # Execute handler
            response_data = await handler(request)
            
            return APIResponse(
                status_code=200,
                body=response_data,
                headers={"Content-Type": "application/json"},
                request_id=request.request_id
            )
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return APIResponse(
                status_code=500,
                body={"error": "Internal server error", "details": str(e)},
                headers={"Content-Type": "application/json"},
                request_id=request.request_id,
                error=str(e)
            )
            
    def _validate_request(self, request: APIRequest) -> Optional[str]:
        """Validate API request."""
        if not request.endpoint:
            return "Missing endpoint"
            
        if not request.method:
            return "Missing method"
            
        # Endpoint-specific validation
        if request.endpoint == APIEndpoint.EXECUTE_RULE:
            if not request.body.get("rule_id") and not request.body.get("rule"):
                return "Missing rule_id or rule definition"
                
        return None
        
    async def _handle_execute_rule(self, request: APIRequest) -> Dict[str, Any]:
        """Handle rule execution request."""
        body = request.body
        
        # Get or create rule
        if "rule_id" in body:
            # Load rule by ID (would query from storage)
            rule = await self._load_rule(body["rule_id"])
        else:
            # Create rule from definition
            rule_data = body["rule"]
            rule = BusinessRule.from_dict(rule_data)
            
        # Get execution context
        context = body.get("context", {})
        
        # Add request metadata to context
        context["_request_id"] = request.request_id
        context["_timestamp"] = request.timestamp.isoformat()
        
        # Execute rule
        results = await self.orchestrator.execute_rule(rule, context)
        
        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "execution_results": results,
            "frameworks_used": list(results.keys()),
            "success": all("error" not in r for r in results.values() if isinstance(r, dict))
        }
        
    async def _handle_create_rule(self, request: APIRequest) -> Dict[str, Any]:
        """Handle rule creation request."""
        rule_data = request.body.get("rule", {})
        
        # Validate rule data
        try:
            rule = BusinessRule.from_dict(rule_data)
        except Exception as e:
            raise ValueError(f"Invalid rule definition: {e}")
            
        # Store rule (would persist to storage)
        await self._store_rule(rule)
        
        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "created": True,
            "message": "Rule created successfully"
        }
        
    async def _handle_list_rules(self, request: APIRequest) -> Dict[str, Any]:
        """Handle list rules request."""
        # Query parameters
        filters = request.query_params
        
        # Load rules (would query from storage)
        rules = await self._load_rules(filters)
        
        return {
            "rules": [rule.to_dict() for rule in rules],
            "total": len(rules),
            "filters": filters
        }
        
    async def _handle_delete_rule(self, request: APIRequest) -> Dict[str, Any]:
        """Handle rule deletion request."""
        rule_id = request.body.get("rule_id")
        
        if not rule_id:
            raise ValueError("Missing rule_id")
            
        # Delete rule (would remove from storage)
        deleted = await self._delete_rule(rule_id)
        
        return {
            "rule_id": rule_id,
            "deleted": deleted,
            "message": "Rule deleted successfully" if deleted else "Rule not found"
        }
        
    async def _handle_framework_status(self, request: APIRequest) -> Dict[str, Any]:
        """Handle framework status request."""
        # Get health status for all frameworks
        health_status = await self.orchestrator.health_check()
        
        return {
            "frameworks": health_status.get("adapters", {}),
            "overall_status": health_status.get("orchestrator", "unknown")
        }
        
    async def _handle_framework_capabilities(self, request: APIRequest) -> Dict[str, Any]:
        """Handle framework capabilities request."""
        capabilities = {}
        
        # Get capabilities for each adapter
        for name, adapter in self.orchestrator.adapters.items():
            capabilities[name] = {
                "capabilities": adapter.get_capabilities(),
                "connected": adapter.is_connected
            }
            
        return {"capabilities": capabilities}
        
    async def _handle_workflow_start(self, request: APIRequest) -> Dict[str, Any]:
        """Handle workflow start request."""
        workflow_type = request.body.get("workflow_type")
        parameters = request.body.get("parameters", {})
        
        # Map workflow type to appropriate scenario
        workflow_handlers = {
            "customer_service": self._start_customer_service_workflow,
            "fraud_detection": self._start_fraud_detection_workflow,
            "inventory_management": self._start_inventory_management_workflow
        }
        
        handler = workflow_handlers.get(workflow_type)
        if not handler:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
        # Start workflow
        workflow_id = await handler(parameters)
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "status": "started",
            "message": f"Workflow {workflow_type} started successfully"
        }
        
    async def _handle_workflow_status(self, request: APIRequest) -> Dict[str, Any]:
        """Handle workflow status request."""
        workflow_id = request.query_params.get("workflow_id")
        
        if not workflow_id:
            raise ValueError("Missing workflow_id")
            
        # Query workflow status (would check with Temporal)
        status = await self._get_workflow_status(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": status.get("status", "unknown"),
            "details": status
        }
        
    async def _handle_health_check(self, request: APIRequest) -> Dict[str, Any]:
        """Handle health check request."""
        health_status = await self.orchestrator.health_check()
        
        # Determine overall health
        all_healthy = all(
            adapter.get("status") == "healthy"
            for adapter in health_status.get("adapters", {}).values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "details": health_status
        }
        
    async def _handle_metrics(self, request: APIRequest) -> Dict[str, Any]:
        """Handle metrics request."""
        # Collect metrics from various sources
        metrics = {
            "rules_executed": 0,  # Would track actual executions
            "frameworks_active": len(self.orchestrator.adapters),
            "average_execution_time": 0,  # Would calculate from history
            "error_rate": 0,  # Would calculate from history
            "event_count": len(self.event_bus.event_history)
        }
        
        return {"metrics": metrics}
        
    # Helper methods (would interact with storage in production)
    
    async def _load_rule(self, rule_id: str) -> BusinessRule:
        """Load rule from storage."""
        # Mock implementation
        return BusinessRule(
            name="mock_rule",
            description="Mock rule for testing"
        )
        
    async def _store_rule(self, rule: BusinessRule) -> None:
        """Store rule to storage."""
        # Mock implementation
        pass
        
    async def _load_rules(self, filters: Dict[str, str]) -> List[BusinessRule]:
        """Load rules from storage with filters."""
        # Mock implementation
        return []
        
    async def _delete_rule(self, rule_id: str) -> bool:
        """Delete rule from storage."""
        # Mock implementation
        return True
        
    async def _start_customer_service_workflow(self, parameters: Dict[str, Any]) -> str:
        """Start customer service workflow."""
        from ..scenarios.customer_service import CustomerServiceWorkflow
        
        workflow = CustomerServiceWorkflow(self.orchestrator, self.event_bus)
        result = await workflow.handle_customer_interaction(parameters)
        
        return f"cs_workflow_{result.get('interaction_id', 'unknown')}"
        
    async def _start_fraud_detection_workflow(self, parameters: Dict[str, Any]) -> str:
        """Start fraud detection workflow."""
        from ..scenarios.fraud_detection import FraudDetectionScenario
        
        scenario = FraudDetectionScenario(self.orchestrator, self.event_bus)
        result = await scenario.analyze_transaction(parameters)
        
        return f"fraud_workflow_{result.get('transaction_id', 'unknown')}"
        
    async def _start_inventory_management_workflow(self, parameters: Dict[str, Any]) -> str:
        """Start inventory management workflow."""
        from ..scenarios.inventory_management import InventoryManagementScenario
        
        scenario = InventoryManagementScenario(self.orchestrator, self.event_bus)
        result = await scenario.manage_product_inventory(parameters)
        
        return f"inventory_workflow_{result.get('product_id', 'unknown')}"
        
    async def _get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        # Mock implementation
        return {
            "status": "running",
            "progress": 50,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    async def translate_request(
        self,
        request: Any,
        source_protocol: ProtocolType,
        target_protocol: ProtocolType = ProtocolType.REST
    ) -> APIRequest:
        """
        Translate request from different protocol to API request.
        
        Args:
            request: Original request
            source_protocol: Source protocol type
            target_protocol: Target protocol type (default REST)
            
        Returns:
            Translated API request
        """
        # Use protocol translator
        translated = await self.protocol_translator.translate_protocol(
            request, source_protocol, target_protocol
        )
        
        # Convert to APIRequest
        return APIRequest(
            endpoint=translated.get("path", "/"),
            method=translated.get("method", "POST"),
            headers=translated.get("headers", {}),
            body=translated.get("body", {}),
            query_params=self._extract_query_params(translated.get("path", ""))
        )
        
    def _extract_query_params(self, path: str) -> Dict[str, str]:
        """Extract query parameters from path."""
        if "?" not in path:
            return {}
            
        query_string = path.split("?")[1]
        params = {}
        
        for param in query_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
                
        return params