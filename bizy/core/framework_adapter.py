"""
Framework Adapter: Base class for framework-specific integrations.

This module provides the abstract base class that all framework adapters
must implement to integrate with the Business Logic Orchestrator.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import asyncio
import logging

from .business_rule import BusinessRule

logger = logging.getLogger(__name__)


class FrameworkAdapter(ABC):
    """
    Abstract base class for framework-specific adapters.
    
    Each supported framework (LangChain, Semantic Kernel, MCP, etc.) must
    implement this interface to participate in business logic orchestration.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the framework."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the framework."""
        pass
        
    @abstractmethod
    async def can_handle_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> bool:
        """
        Determine if this adapter can handle the given business rule.
        
        Args:
            rule: Business rule to evaluate
            context: Execution context
            
        Returns:
            True if this adapter can execute the rule, False otherwise
        """
        pass
        
    @abstractmethod
    async def execute_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a business rule using this framework.
        
        Args:
            rule: Business rule to execute
            context: Execution context and input data
            
        Returns:
            Execution results
        """
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the framework connection.
        
        Returns:
            Health status information
        """
        pass
        
    async def initialize(self) -> None:
        """Initialize the adapter and establish framework connection."""
        try:
            await self.connect()
            self.is_connected = True
            logger.info(f"Adapter {self.name} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize adapter {self.name}: {e}")
            raise
            
    async def shutdown(self) -> None:
        """Shutdown the adapter and clean up resources."""
        try:
            await self.disconnect()
            self.is_connected = False
            logger.info(f"Adapter {self.name} shutdown successfully")
        except Exception as e:
            logger.error(f"Error during adapter {self.name} shutdown: {e}")
            
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities supported by this adapter.
        
        Returns:
            List of capability names
        """
        return getattr(self, 'capabilities', [])
        
    def supports_capability(self, capability: str) -> bool:
        """Check if adapter supports a specific capability."""
        return capability in self.get_capabilities()


class BaseFrameworkAdapter(FrameworkAdapter):
    """
    Base implementation with common functionality for framework adapters.
    
    Provides default implementations and utility methods that can be
    used by specific framework adapters.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.capabilities = []
        self.connection_timeout = config.get('connection_timeout', 30.0)
        self.execution_timeout = config.get('execution_timeout', 60.0)
        
    async def can_handle_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> bool:
        """
        Default implementation checks if any rule actions target this framework.
        
        Override in specific adapters for more sophisticated rule evaluation.
        """
        applicable_actions = rule.get_applicable_actions([self.name])
        return len(applicable_actions) > 0
        
    async def execute_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default implementation executes all applicable actions sequentially.
        
        Override in specific adapters for more sophisticated execution patterns.
        """
        results = {
            "adapter": self.name,
            "rule_id": rule.id,
            "actions_executed": [],
            "errors": []
        }
        
        applicable_actions = rule.get_applicable_actions([self.name])
        
        for action in applicable_actions:
            try:
                action_result = await self._execute_action(action, context)
                results["actions_executed"].append({
                    "action": action.action,
                    "result": action_result
                })
            except Exception as e:
                logger.error(f"Action {action.action} failed: {e}")
                results["errors"].append({
                    "action": action.action,
                    "error": str(e)
                })
                
        return results
        
    @abstractmethod
    async def _execute_action(self, action, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action on this framework.
        
        Must be implemented by specific framework adapters.
        """
        pass
        
    async def health_check(self) -> Dict[str, Any]:
        """Default health check implementation."""
        return {
            "adapter": self.name,
            "status": "healthy" if self.is_connected else "disconnected",
            "capabilities": self.get_capabilities(),
            "config": {k: v for k, v in self.config.items() if not k.endswith('_secret')}
        }


class AdapterRegistry:
    """Registry for managing framework adapters."""
    
    def __init__(self):
        self.adapters: Dict[str, FrameworkAdapter] = {}
        
    def register(self, adapter: FrameworkAdapter) -> None:
        """Register a framework adapter."""
        self.adapters[adapter.name] = adapter
        logger.info(f"Registered adapter: {adapter.name}")
        
    def unregister(self, name: str) -> None:
        """Unregister a framework adapter."""
        if name in self.adapters:
            del self.adapters[name]
            logger.info(f"Unregistered adapter: {name}")
            
    def get_adapter(self, name: str) -> Optional[FrameworkAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)
        
    def get_all_adapters(self) -> Dict[str, FrameworkAdapter]:
        """Get all registered adapters."""
        return self.adapters.copy()
        
    async def initialize_all(self) -> None:
        """Initialize all registered adapters."""
        tasks = []
        for adapter in self.adapters.values():
            tasks.append(adapter.initialize())
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def shutdown_all(self) -> None:
        """Shutdown all registered adapters."""
        tasks = []
        for adapter in self.adapters.values():
            tasks.append(adapter.shutdown())
            
        await asyncio.gather(*tasks, return_exceptions=True)
