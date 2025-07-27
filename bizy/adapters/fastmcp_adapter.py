"""
FastMCP Adapter: Integration with FastMCP for high-performance tool coordination.

This module provides the adapter for executing business rules through
FastMCP's optimized tool execution and coordination capabilities.
"""

from typing import Any, Dict, List, Optional, Callable
import logging
import asyncio
import time

from ..core.framework_adapter import BaseFrameworkAdapter
from ..core.business_rule import BusinessRule, RuleAction

logger = logging.getLogger(__name__)


class FastMCPAdapter(BaseFrameworkAdapter):
    """
    Adapter for integrating FastMCP with the Business Logic Orchestrator.
    
    Provides capabilities for:
    - High-performance tool execution
    - Tool transformation and optimization
    - Batch processing
    - Caching and memoization
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("fastmcp", config)
        self.capabilities = [
            "tool_optimization",
            "batch_processing",
            "caching",
            "parallel_execution",
            "tool_transformation",
            "performance_monitoring"
        ]
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.tool_cache: Dict[str, Any] = {}
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        self.batch_size = config.get("default_batch_size", 10)
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes default
        
    async def connect(self) -> None:
        """Initialize FastMCP adapter and optimize for performance."""
        try:
            # Initialize performance monitoring
            self.execution_stats = {
                "total_executions": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "average_execution_time": 0.0
            }
            
            # Register built-in optimized tools
            await self._register_optimized_tools()
            
            # Initialize tool transformation pipeline
            await self._initialize_transformations()
            
            self.is_connected = True
            logger.info("FastMCP adapter connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect FastMCP adapter: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect and cleanup resources."""
        try:
            # Clear caches
            self.tool_cache.clear()
            self.tools.clear()
            
            # Log final statistics
            logger.info(f"FastMCP execution stats: {self.execution_stats}")
            
            self.is_connected = False
            logger.info("FastMCP adapter disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting FastMCP adapter: {e}")
            
    async def _execute_action(self, action: RuleAction, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action using FastMCP optimizations.
        
        Supported actions:
        - execute_tool: Execute a tool with optimizations
        - batch_execute: Execute tools in batch
        - transform_tool: Apply transformations to tool
        - cache_result: Cache tool execution result
        """
        action_type = action.action
        params = action.parameters
        
        try:
            if action_type == "execute_tool":
                return await self._execute_tool_optimized(params, context)
            elif action_type == "batch_execute":
                return await self._batch_execute_tools(params, context)
            elif action_type == "transform_tool":
                return await self._transform_tool(params, context)
            elif action_type == "cache_result":
                return await self._cache_tool_result(params, context)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing FastMCP action {action_type}: {e}")
            raise
            
    async def _execute_tool_optimized(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with performance optimizations."""
        tool_name = params.get("tool_name")
        tool_params = params.get("parameters", {})
        use_cache = params.get("use_cache", True)
        
        # Check cache first
        cache_key = self._generate_cache_key(tool_name, tool_params)
        if use_cache and cache_key in self.tool_cache:
            cached_result = self.tool_cache[cache_key]
            if time.time() - cached_result["timestamp"] < self.cache_ttl:
                self.execution_stats["cache_hits"] += 1
                return {
                    "tool_name": tool_name,
                    "result": cached_result["result"],
                    "cached": True,
                    "execution_time": 0.0
                }
        
        self.execution_stats["cache_misses"] += 1
        
        # Execute tool with timing
        start_time = time.time()
        
        # Get tool definition
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
            
        # Apply optimizations
        optimized_params = await self._optimize_parameters(tool_name, tool_params, context)
        
        # Execute tool
        result = await self._execute_tool_internal(tool, optimized_params)
        
        execution_time = time.time() - start_time
        
        # Update statistics
        self._update_execution_stats(execution_time)
        
        # Cache result if enabled
        if use_cache:
            self.tool_cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            
        return {
            "tool_name": tool_name,
            "result": result,
            "cached": False,
            "execution_time": execution_time,
            "optimizations_applied": True
        }
        
    async def _batch_execute_tools(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple tools in batch for better performance."""
        tool_executions = params.get("executions", [])
        parallel = params.get("parallel", True)
        
        results = []
        total_start_time = time.time()
        
        if parallel:
            # Execute tools in parallel
            tasks = []
            for execution in tool_executions:
                task = self._execute_tool_optimized(execution, context)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute tools sequentially
            for execution in tool_executions:
                result = await self._execute_tool_optimized(execution, context)
                results.append(result)
                
        total_execution_time = time.time() - total_start_time
        
        # Process results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "index": i,
                    "execution": tool_executions[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
                
        return {
            "batch_size": len(tool_executions),
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "results": successful_results,
            "errors": failed_results,
            "total_execution_time": total_execution_time,
            "parallel_execution": parallel
        }
        
    async def _transform_tool(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to optimize tool execution."""
        tool_name = params.get("tool_name")
        transformation = params.get("transformation", "optimize")
        
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
            
        transformed_tool = None
        
        if transformation == "optimize":
            # Apply general optimizations
            transformed_tool = await self._apply_optimizations(tool)
        elif transformation == "parallelize":
            # Transform for parallel execution
            transformed_tool = await self._parallelize_tool(tool)
        elif transformation == "cache":
            # Add caching layer
            transformed_tool = await self._add_caching_layer(tool)
        elif transformation == "batch":
            # Transform for batch processing
            transformed_tool = await self._batchify_tool(tool)
            
        # Register transformed tool
        transformed_name = f"{tool_name}_{transformation}"
        self.tools[transformed_name] = transformed_tool
        
        return {
            "original_tool": tool_name,
            "transformation": transformation,
            "transformed_tool_name": transformed_name,
            "optimizations": transformed_tool.get("optimizations", [])
        }
        
    async def _cache_tool_result(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Explicitly cache a tool execution result."""
        tool_name = params.get("tool_name")
        tool_params = params.get("parameters", {})
        result = params.get("result")
        ttl = params.get("ttl", self.cache_ttl)
        
        cache_key = self._generate_cache_key(tool_name, tool_params)
        
        self.tool_cache[cache_key] = {
            "result": result,
            "timestamp": time.time(),
            "ttl": ttl
        }
        
        return {
            "tool_name": tool_name,
            "cache_key": cache_key,
            "cached": True,
            "ttl": ttl
        }
        
    async def _register_optimized_tools(self) -> None:
        """Register built-in optimized tools."""
        
        # Fast calculator tool
        async def fast_calculator(params: Dict[str, Any]) -> Any:
            expression = params.get("expression", "")
            try:
                # Use compile for better performance
                compiled = compile(expression, "<string>", "eval")
                return eval(compiled)
            except:
                return None
                
        self.tools["fast_calculator"] = {
            "function": fast_calculator,
            "description": "Optimized calculator for mathematical expressions",
            "optimizations": ["compiled", "cached"]
        }
        
        # Batch data processor
        async def batch_processor(params: Dict[str, Any]) -> Any:
            data = params.get("data", [])
            operation = params.get("operation", "transform")
            
            if operation == "transform":
                return [item.upper() if isinstance(item, str) else item for item in data]
            elif operation == "filter":
                filter_func = params.get("filter", lambda x: True)
                return [item for item in data if filter_func(item)]
            elif operation == "aggregate":
                return {
                    "count": len(data),
                    "first": data[0] if data else None,
                    "last": data[-1] if data else None
                }
                
        self.tools["batch_processor"] = {
            "function": batch_processor,
            "description": "Optimized batch data processing",
            "optimizations": ["vectorized", "parallel"]
        }
        
        # Cache lookup tool
        async def cache_lookup(params: Dict[str, Any]) -> Any:
            key = params.get("key")
            return self.tool_cache.get(key, {"found": False})
            
        self.tools["cache_lookup"] = {
            "function": cache_lookup,
            "description": "Direct cache access tool",
            "optimizations": ["direct_access"]
        }
        
    async def _initialize_transformations(self) -> None:
        """Initialize tool transformation pipeline."""
        self.transformations = {
            "memoize": self._memoize_transformation,
            "parallelize": self._parallelize_transformation,
            "batch": self._batch_transformation,
            "cache": self._cache_transformation
        }
        
    async def _optimize_parameters(self, tool_name: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize tool parameters before execution."""
        optimized = params.copy()
        
        # Apply context-aware optimizations
        if "batch_size" not in optimized and "data" in optimized:
            data_size = len(optimized.get("data", []))
            optimized["batch_size"] = min(self.batch_size, data_size)
            
        # Merge with context for additional optimization opportunities
        for key, value in context.items():
            if key.startswith("optimize_") and key[9:] in optimized:
                optimized[key[9:]] = value
                
        return optimized
        
    async def _execute_tool_internal(self, tool: Dict[str, Any], params: Dict[str, Any]) -> Any:
        """Internal tool execution with monitoring."""
        func = tool.get("function")
        if not func:
            raise ValueError("Tool missing function implementation")
            
        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(params)
        else:
            result = func(params)
            
        self.execution_stats["total_executions"] += 1
        
        return result
        
    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key for tool execution."""
        import hashlib
        import json
        
        key_data = {
            "tool": tool_name,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
        
    def _update_execution_stats(self, execution_time: float) -> None:
        """Update execution statistics."""
        stats = self.execution_stats
        total = stats["total_executions"]
        current_avg = stats["average_execution_time"]
        
        # Calculate new average
        new_avg = ((current_avg * (total - 1)) + execution_time) / total
        stats["average_execution_time"] = new_avg
        
    async def _apply_optimizations(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Apply general optimizations to a tool."""
        optimized = tool.copy()
        optimized["optimizations"] = tool.get("optimizations", []) + ["general_optimization"]
        return optimized
        
    async def _parallelize_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Transform tool for parallel execution."""
        parallelized = tool.copy()
        parallelized["optimizations"] = tool.get("optimizations", []) + ["parallelized"]
        parallelized["parallel"] = True
        return parallelized
        
    async def _add_caching_layer(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Add caching layer to tool."""
        cached = tool.copy()
        cached["optimizations"] = tool.get("optimizations", []) + ["cached"]
        cached["cache_enabled"] = True
        return cached
        
    async def _batchify_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Transform tool for batch processing."""
        batched = tool.copy()
        batched["optimizations"] = tool.get("optimizations", []) + ["batched"]
        batched["batch_enabled"] = True
        return batched
        
    # Transformation functions
    async def _memoize_transformation(self, func: Callable) -> Callable:
        """Add memoization to a function."""
        cache = {}
        
        async def memoized(*args, **kwargs):
            key = str((args, sorted(kwargs.items())))
            if key in cache:
                return cache[key]
            result = await func(*args, **kwargs)
            cache[key] = result
            return result
            
        return memoized
        
    async def _parallelize_transformation(self, func: Callable) -> Callable:
        """Transform function for parallel execution."""
        async def parallelized(items: List[Any]) -> List[Any]:
            tasks = [func(item) for item in items]
            return await asyncio.gather(*tasks)
            
        return parallelized
        
    async def _batch_transformation(self, func: Callable) -> Callable:
        """Transform function for batch processing."""
        async def batched(items: List[Any], batch_size: int = 10) -> List[Any]:
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                batch_results = await func(batch)
                results.extend(batch_results)
            return results
            
        return batched
        
    async def _cache_transformation(self, func: Callable) -> Callable:
        """Add caching to a function."""
        async def cached(*args, **kwargs):
            cache_key = self._generate_cache_key(func.__name__, {"args": args, "kwargs": kwargs})
            if cache_key in self.tool_cache:
                return self.tool_cache[cache_key]["result"]
            result = await func(*args, **kwargs)
            self.tool_cache[cache_key] = {"result": result, "timestamp": time.time()}
            return result
            
        return cached
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on FastMCP adapter."""
        health_status = await super().health_check()
        
        # Add FastMCP-specific metrics
        health_status.update({
            "tools_registered": len(self.tools),
            "cache_size": len(self.tool_cache),
            "execution_stats": self.execution_stats,
            "cache_hit_rate": (
                self.execution_stats["cache_hits"] / 
                max(1, self.execution_stats["cache_hits"] + self.execution_stats["cache_misses"])
            ) * 100,
            "average_execution_time_ms": self.execution_stats["average_execution_time"] * 1000
        })
        
        return health_status