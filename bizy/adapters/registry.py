"""
Adapter Registry: Central registry for framework adapter management.

This module provides registration, discovery, and lifecycle management
for all framework adapters in the system.
"""

from typing import Any, Dict, List, Optional, Type
import logging
import asyncio
from enum import Enum

from ..core.framework_adapter import FrameworkAdapter
from .langchain_adapter import LangChainAdapter
from .semantic_kernel_adapter import SemanticKernelAdapter
from .mcp_adapter import MCPAdapter
from .temporal_adapter import TemporalAdapter
from .fastmcp_adapter import FastMCPAdapter
from .zep_adapter import ZepAdapter

logger = logging.getLogger(__name__)


class AdapterType(str, Enum):
    """Supported adapter types."""
    LANGCHAIN = "langchain"
    SEMANTIC_KERNEL = "semantic_kernel"
    MCP = "mcp"
    TEMPORAL = "temporal"
    FASTMCP = "fastmcp"
    ZEP = "zep"


class AdapterRegistry:
    """
    Central registry for managing framework adapters.
    
    Provides:
    - Adapter registration and discovery
    - Lifecycle management
    - Health monitoring
    - Configuration management
    """
    
    # Adapter class mappings
    ADAPTER_CLASSES: Dict[AdapterType, Type[FrameworkAdapter]] = {
        AdapterType.LANGCHAIN: LangChainAdapter,
        AdapterType.SEMANTIC_KERNEL: SemanticKernelAdapter,
        AdapterType.MCP: MCPAdapter,
        AdapterType.TEMPORAL: TemporalAdapter,
        AdapterType.FASTMCP: FastMCPAdapter,
        AdapterType.ZEP: ZepAdapter
    }
    
    def __init__(self):
        self.adapters: Dict[str, FrameworkAdapter] = {}
        self.adapter_configs: Dict[str, Dict[str, Any]] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        
    async def register_adapter(
        self,
        adapter_type: AdapterType,
        config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> FrameworkAdapter:
        """
        Register a new framework adapter.
        
        Args:
            adapter_type: Type of adapter to register
            config: Configuration for the adapter
            name: Optional custom name (defaults to adapter type)
            
        Returns:
            Registered adapter instance
        """
        # Use adapter type as name if not provided
        if not name:
            name = adapter_type.value
            
        # Check if already registered
        if name in self.adapters:
            raise ValueError(f"Adapter already registered: {name}")
            
        # Get adapter class
        adapter_class = self.ADAPTER_CLASSES.get(adapter_type)
        if not adapter_class:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
            
        # Create adapter instance
        adapter_config = config or {}
        adapter = adapter_class(adapter_config)
        
        # Initialize adapter
        try:
            await adapter.initialize()
            
            # Register adapter
            self.adapters[name] = adapter
            self.adapter_configs[name] = adapter_config
            
            # Initial health check
            self.health_status[name] = await adapter.health_check()
            
            logger.info(f"Registered adapter: {name} ({adapter_type.value})")
            
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to register adapter {name}: {e}")
            raise
            
    async def unregister_adapter(self, name: str) -> None:
        """
        Unregister and shutdown an adapter.
        
        Args:
            name: Name of adapter to unregister
        """
        if name not in self.adapters:
            raise ValueError(f"Adapter not found: {name}")
            
        adapter = self.adapters[name]
        
        try:
            # Shutdown adapter
            await adapter.shutdown()
            
            # Remove from registry
            del self.adapters[name]
            del self.adapter_configs[name]
            del self.health_status[name]
            
            logger.info(f"Unregistered adapter: {name}")
            
        except Exception as e:
            logger.error(f"Error unregistering adapter {name}: {e}")
            raise
            
    def get_adapter(self, name: str) -> Optional[FrameworkAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)
        
    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self.adapters.keys())
        
    def get_adapters_by_capability(self, capability: str) -> List[Tuple[str, FrameworkAdapter]]:
        """
        Get all adapters that support a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of (name, adapter) tuples
        """
        matching_adapters = []
        
        for name, adapter in self.adapters.items():
            if adapter.supports_capability(capability):
                matching_adapters.append((name, adapter))
                
        return matching_adapters
        
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all registered adapters.
        
        Returns:
            Health status for all adapters
        """
        health_tasks = {}
        
        # Create health check tasks
        for name, adapter in self.adapters.items():
            health_tasks[name] = adapter.health_check()
            
        # Execute health checks concurrently
        health_results = await asyncio.gather(
            *health_tasks.values(),
            return_exceptions=True
        )
        
        # Process results
        health_status = {}
        for i, (name, _) in enumerate(health_tasks.items()):
            result = health_results[i]
            
            if isinstance(result, Exception):
                health_status[name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
            else:
                health_status[name] = result
                
        # Update cached status
        self.health_status = health_status
        
        return health_status
        
    async def initialize_all(self) -> None:
        """Initialize all registered adapters."""
        init_tasks = []
        
        for adapter in self.adapters.values():
            if not adapter.is_connected:
                init_tasks.append(adapter.initialize())
                
        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)
            
    async def shutdown_all(self) -> None:
        """Shutdown all registered adapters."""
        shutdown_tasks = []
        
        for adapter in self.adapters.values():
            shutdown_tasks.append(adapter.shutdown())
            
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            
    def get_adapter_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about an adapter.
        
        Args:
            name: Adapter name
            
        Returns:
            Adapter information including config, capabilities, and health
        """
        adapter = self.get_adapter(name)
        if not adapter:
            raise ValueError(f"Adapter not found: {name}")
            
        return {
            "name": name,
            "type": adapter.__class__.__name__,
            "connected": adapter.is_connected,
            "capabilities": adapter.get_capabilities(),
            "config": self.adapter_configs.get(name, {}),
            "health": self.health_status.get(name, {})
        }
        
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry."""
        total_adapters = len(self.adapters)
        connected_adapters = sum(1 for a in self.adapters.values() if a.is_connected)
        
        # Count capabilities
        all_capabilities = set()
        for adapter in self.adapters.values():
            all_capabilities.update(adapter.get_capabilities())
            
        # Group adapters by type
        adapters_by_type = {}
        for name, adapter in self.adapters.items():
            adapter_type = adapter.__class__.__name__
            if adapter_type not in adapters_by_type:
                adapters_by_type[adapter_type] = []
            adapters_by_type[adapter_type].append(name)
            
        return {
            "total_adapters": total_adapters,
            "connected_adapters": connected_adapters,
            "disconnected_adapters": total_adapters - connected_adapters,
            "unique_capabilities": len(all_capabilities),
            "capabilities": list(all_capabilities),
            "adapters_by_type": adapters_by_type,
            "health_summary": {
                "healthy": sum(1 for h in self.health_status.values() 
                             if h.get("status") == "healthy"),
                "unhealthy": sum(1 for h in self.health_status.values() 
                               if h.get("status") != "healthy")
            }
        }
        
    async def reload_adapter(self, name: str) -> FrameworkAdapter:
        """
        Reload an adapter with its current configuration.
        
        Args:
            name: Adapter name
            
        Returns:
            Reloaded adapter instance
        """
        if name not in self.adapters:
            raise ValueError(f"Adapter not found: {name}")
            
        # Get current adapter info
        adapter = self.adapters[name]
        adapter_type = None
        
        # Find adapter type
        for atype, aclass in self.ADAPTER_CLASSES.items():
            if isinstance(adapter, aclass):
                adapter_type = atype
                break
                
        if not adapter_type:
            raise ValueError(f"Unknown adapter type for: {name}")
            
        config = self.adapter_configs.get(name, {})
        
        # Unregister old adapter
        await self.unregister_adapter(name)
        
        # Register new adapter with same config
        return await self.register_adapter(adapter_type, config, name)


# Global registry instance
_global_registry: Optional[AdapterRegistry] = None


def get_global_registry() -> AdapterRegistry:
    """Get the global adapter registry instance."""
    global _global_registry
    
    if _global_registry is None:
        _global_registry = AdapterRegistry()
        
    return _global_registry


async def setup_default_adapters(config: Optional[Dict[str, Any]] = None) -> AdapterRegistry:
    """
    Set up the default set of adapters with optional configuration.
    
    Args:
        config: Configuration dictionary with adapter-specific configs
        
    Returns:
        Configured adapter registry
    """
    registry = get_global_registry()
    config = config or {}
    
    # Register default adapters
    adapters_to_register = [
        (AdapterType.LANGCHAIN, config.get("langchain", {})),
        (AdapterType.SEMANTIC_KERNEL, config.get("semantic_kernel", {})),
        (AdapterType.MCP, config.get("mcp", {})),
        (AdapterType.TEMPORAL, config.get("temporal", {})),
        (AdapterType.FASTMCP, config.get("fastmcp", {})),
        (AdapterType.ZEP, config.get("zep", {}))
    ]
    
    for adapter_type, adapter_config in adapters_to_register:
        try:
            await registry.register_adapter(adapter_type, adapter_config)
        except Exception as e:
            logger.warning(f"Failed to register {adapter_type.value} adapter: {e}")
            
    return registry