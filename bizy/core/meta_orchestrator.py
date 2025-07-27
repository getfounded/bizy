"""
Meta-Orchestrator: Core coordination engine for cross-framework business logic.

This module provides the central orchestration layer that coordinates business
rule execution across multiple AI frameworks.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import asyncio
import logging

from .business_rule import BusinessRule
from .framework_adapter import FrameworkAdapter
from ..events.event_bus import EventBus

logger = logging.getLogger(__name__)


class MetaOrchestrator:
    """
    Central coordination engine that executes business rules across multiple frameworks.
    
    The MetaOrchestrator translates framework-agnostic business rules into
    native execution patterns for each registered framework adapter.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.adapters: Dict[str, FrameworkAdapter] = {}
        self.event_bus = event_bus or EventBus()
        self.active_rules: List[BusinessRule] = []
        
    def register_adapter(self, name: str, adapter: FrameworkAdapter) -> None:
        """Register a framework adapter for business rule execution."""
        self.adapters[name] = adapter
        logger.info(f"Registered adapter: {name}")
        
    def unregister_adapter(self, name: str) -> None:
        """Unregister a framework adapter."""
        if name in self.adapters:
            del self.adapters[name]
            logger.info(f"Unregistered adapter: {name}")
            
    async def execute_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a business rule across applicable framework adapters.
        
        Args:
            rule: The business rule to execute
            context: Execution context and input data
            
        Returns:
            Execution results from all applicable adapters
        """
        results = {}
        
        # Determine which adapters can handle this rule
        applicable_adapters = await self._get_applicable_adapters(rule, context)
        
        # Execute rule on each applicable adapter
        tasks = []
        for adapter_name, adapter in applicable_adapters.items():
            task = self._execute_on_adapter(adapter_name, adapter, rule, context)
            tasks.append(task)
            
        # Wait for all executions to complete
        adapter_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, (adapter_name, _) in enumerate(applicable_adapters.items()):
            result = adapter_results[i]
            if isinstance(result, Exception):
                logger.error(f"Adapter {adapter_name} failed: {result}")
                results[adapter_name] = {"error": str(result)}
            else:
                results[adapter_name] = result
                
        return results
        
    async def _get_applicable_adapters(
        self, rule: BusinessRule, context: Dict[str, Any]
    ) -> Dict[str, FrameworkAdapter]:
        """Determine which adapters can handle the given rule."""
        applicable = {}
        
        for name, adapter in self.adapters.items():
            if await adapter.can_handle_rule(rule, context):
                applicable[name] = adapter
                
        return applicable
        
    async def _execute_on_adapter(
        self, 
        adapter_name: str, 
        adapter: FrameworkAdapter, 
        rule: BusinessRule, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a rule on a specific adapter with error handling."""
        try:
            # Publish execution start event
            await self.event_bus.publish(
                "rule_execution_started",
                {
                    "adapter": adapter_name,
                    "rule_id": rule.id,
                    "context": context
                }
            )
            
            # Execute the rule
            result = await adapter.execute_rule(rule, context)
            
            # Publish execution success event
            await self.event_bus.publish(
                "rule_execution_completed",
                {
                    "adapter": adapter_name,
                    "rule_id": rule.id,
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            # Publish execution failure event
            await self.event_bus.publish(
                "rule_execution_failed",
                {
                    "adapter": adapter_name,
                    "rule_id": rule.id,
                    "error": str(e)
                }
            )
            raise
            
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered adapters."""
        health_status = {
            "orchestrator": "healthy",
            "adapters": {}
        }
        
        for name, adapter in self.adapters.items():
            try:
                adapter_health = await adapter.health_check()
                health_status["adapters"][name] = adapter_health
            except Exception as e:
                health_status["adapters"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                
        return health_status
