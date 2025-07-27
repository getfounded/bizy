"""
Load Balancer: Distributes business rule execution across framework instances.

This module provides load balancing capabilities for optimal resource
utilization and high availability.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import logging
import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class BalancingStrategy(str, Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESPONSE_TIME = "response_time"
    RESOURCE_BASED = "resource_based"
    CAPABILITY_BASED = "capability_based"


@dataclass
class FrameworkInstance:
    """Represents a framework instance for load balancing."""
    name: str
    instance_id: str
    adapter: Any
    weight: float = 1.0
    max_connections: int = 100
    current_connections: int = 0
    total_requests: int = 0
    total_errors: int = 0
    average_response_time: float = 0.0
    last_health_check: float = 0.0
    health_score: float = 1.0
    capabilities: Set[str] = field(default_factory=set)
    
    def is_healthy(self) -> bool:
        """Check if instance is healthy."""
        return self.health_score > 0.5 and self.current_connections < self.max_connections
        
    def update_response_time(self, response_time: float):
        """Update average response time."""
        # Exponential moving average
        alpha = 0.3
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                alpha * response_time + (1 - alpha) * self.average_response_time
            )


class LoadBalancer:
    """
    Distributes business rule execution across multiple framework instances.
    
    Features:
    - Multiple balancing strategies
    - Health monitoring
    - Automatic failover
    - Performance tracking
    - Capability-aware routing
    """
    
    def __init__(self, strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.instances: Dict[str, List[FrameworkInstance]] = defaultdict(list)
        self.round_robin_indices: Dict[str, int] = defaultdict(int)
        self.health_check_interval = 30.0  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        
    def register_instance(self, framework: str, instance: FrameworkInstance):
        """Register a framework instance."""
        self.instances[framework].append(instance)
        logger.info(f"Registered instance {instance.instance_id} for framework {framework}")
        
    def unregister_instance(self, framework: str, instance_id: str):
        """Unregister a framework instance."""
        self.instances[framework] = [
            inst for inst in self.instances[framework]
            if inst.instance_id != instance_id
        ]
        logger.info(f"Unregistered instance {instance_id} for framework {framework}")
        
    async def select_instance(
        self,
        framework: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[FrameworkInstance]:
        """
        Select an instance for execution based on strategy.
        
        Args:
            framework: Framework type
            requirements: Optional requirements (e.g., capabilities)
            
        Returns:
            Selected instance or None if none available
        """
        available_instances = self._get_available_instances(framework, requirements)
        
        if not available_instances:
            return None
            
        if self.strategy == BalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(framework, available_instances)
        elif self.strategy == BalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(available_instances)
        elif self.strategy == BalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(framework, available_instances)
        elif self.strategy == BalancingStrategy.RESPONSE_TIME:
            return self._response_time_select(available_instances)
        elif self.strategy == BalancingStrategy.RESOURCE_BASED:
            return self._resource_based_select(available_instances)
        elif self.strategy == BalancingStrategy.CAPABILITY_BASED:
            return self._capability_based_select(available_instances, requirements)
        else:
            return random.choice(available_instances)
            
    def _get_available_instances(
        self,
        framework: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> List[FrameworkInstance]:
        """Get available instances that meet requirements."""
        instances = self.instances.get(framework, [])
        
        # Filter healthy instances
        available = [inst for inst in instances if inst.is_healthy()]
        
        # Apply requirements filter
        if requirements:
            required_capabilities = requirements.get("capabilities", set())
            if required_capabilities:
                available = [
                    inst for inst in available
                    if required_capabilities.issubset(inst.capabilities)
                ]
                
        return available
        
    def _round_robin_select(
        self,
        framework: str,
        instances: List[FrameworkInstance]
    ) -> FrameworkInstance:
        """Select using round-robin strategy."""
        index = self.round_robin_indices[framework] % len(instances)
        self.round_robin_indices[framework] = index + 1
        return instances[index]
        
    def _least_connections_select(
        self,
        instances: List[FrameworkInstance]
    ) -> FrameworkInstance:
        """Select instance with least connections."""
        return min(instances, key=lambda x: x.current_connections)
        
    def _weighted_round_robin_select(
        self,
        framework: str,
        instances: List[FrameworkInstance]
    ) -> FrameworkInstance:
        """Select using weighted round-robin strategy."""
        # Create weighted list
        weighted_instances = []
        for instance in instances:
            weight = int(instance.weight * 10)  # Scale weight
            weighted_instances.extend([instance] * weight)
            
        if not weighted_instances:
            return instances[0]
            
        index = self.round_robin_indices[framework] % len(weighted_instances)
        self.round_robin_indices[framework] = index + 1
        return weighted_instances[index]
        
    def _response_time_select(
        self,
        instances: List[FrameworkInstance]
    ) -> FrameworkInstance:
        """Select instance with best response time."""
        # Filter instances with response time data
        instances_with_data = [
            inst for inst in instances
            if inst.average_response_time > 0
        ]
        
        if not instances_with_data:
            return random.choice(instances)
            
        return min(instances_with_data, key=lambda x: x.average_response_time)
        
    def _resource_based_select(
        self,
        instances: List[FrameworkInstance]
    ) -> FrameworkInstance:
        """Select based on resource availability."""
        # Calculate resource score
        def resource_score(instance: FrameworkInstance) -> float:
            # Lower is better
            connection_ratio = instance.current_connections / instance.max_connections
            error_ratio = instance.total_errors / max(1, instance.total_requests)
            
            return connection_ratio + error_ratio
            
        return min(instances, key=resource_score)
        
    def _capability_based_select(
        self,
        instances: List[FrameworkInstance],
        requirements: Optional[Dict[str, Any]] = None
    ) -> FrameworkInstance:
        """Select based on capability match."""
        if not requirements:
            return random.choice(instances)
            
        required_capabilities = set(requirements.get("capabilities", []))
        preferred_capabilities = set(requirements.get("preferred_capabilities", []))
        
        # Score instances by capability match
        def capability_score(instance: FrameworkInstance) -> float:
            # Higher is better
            required_match = len(required_capabilities & instance.capabilities)
            preferred_match = len(preferred_capabilities & instance.capabilities)
            
            return required_match * 10 + preferred_match
            
        return max(instances, key=capability_score)
        
    async def execute_with_balancing(
        self,
        framework: str,
        execute_func: Callable,
        requirements: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Tuple[Any, FrameworkInstance]:
        """
        Execute function on selected instance with retry logic.
        
        Args:
            framework: Framework type
            execute_func: Function to execute
            requirements: Optional requirements
            retry_count: Number of retry attempts
            
        Returns:
            Tuple of (result, instance used)
        """
        last_error = None
        tried_instances = set()
        
        for attempt in range(retry_count):
            # Select instance
            instance = await self.select_instance(framework, requirements)
            
            if not instance:
                raise ValueError(f"No available instances for framework {framework}")
                
            # Skip if already tried
            if instance.instance_id in tried_instances:
                continue
                
            tried_instances.add(instance.instance_id)
            
            # Track connection
            instance.current_connections += 1
            instance.total_requests += 1
            
            start_time = time.time()
            
            try:
                # Execute function
                result = await execute_func(instance.adapter)
                
                # Update metrics
                response_time = time.time() - start_time
                instance.update_response_time(response_time)
                
                return result, instance
                
            except Exception as e:
                last_error = e
                instance.total_errors += 1
                
                # Update health score
                instance.health_score *= 0.9  # Decay health score
                
                logger.warning(
                    f"Execution failed on instance {instance.instance_id}: {e}"
                )
                
            finally:
                instance.current_connections -= 1
                
        # All retries failed
        raise Exception(f"Execution failed after {retry_count} attempts: {last_error}")
        
    async def start_health_monitoring(self):
        """Start background health monitoring."""
        if self.health_check_task:
            return
            
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started load balancer health monitoring")
        
    async def stop_health_monitoring(self):
        """Stop background health monitoring."""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
            logger.info("Stopped load balancer health monitoring")
            
    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                
    async def _perform_health_checks(self):
        """Perform health checks on all instances."""
        for framework, instances in self.instances.items():
            for instance in instances:
                try:
                    # Perform health check
                    health_result = await instance.adapter.health_check()
                    
                    # Update health score
                    if health_result.get("status") == "healthy":
                        instance.health_score = min(1.0, instance.health_score * 1.1)
                    else:
                        instance.health_score *= 0.8
                        
                    instance.last_health_check = time.time()
                    
                except Exception as e:
                    logger.error(
                        f"Health check failed for instance {instance.instance_id}: {e}"
                    )
                    instance.health_score *= 0.7
                    
    def get_instance_stats(self, framework: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for instances."""
        stats = {}
        
        frameworks = [framework] if framework else self.instances.keys()
        
        for fw in frameworks:
            instances = self.instances.get(fw, [])
            
            if not instances:
                continue
                
            fw_stats = {
                "total_instances": len(instances),
                "healthy_instances": sum(1 for i in instances if i.is_healthy()),
                "total_connections": sum(i.current_connections for i in instances),
                "total_requests": sum(i.total_requests for i in instances),
                "total_errors": sum(i.total_errors for i in instances),
                "average_response_time": sum(i.average_response_time for i in instances) / len(instances) if instances else 0,
                "instances": []
            }
            
            for instance in instances:
                fw_stats["instances"].append({
                    "instance_id": instance.instance_id,
                    "health_score": instance.health_score,
                    "current_connections": instance.current_connections,
                    "total_requests": instance.total_requests,
                    "error_rate": instance.total_errors / max(1, instance.total_requests),
                    "average_response_time": instance.average_response_time
                })
                
            stats[fw] = fw_stats
            
        return stats
        
    def rebalance_weights(self, performance_window: float = 3600.0):
        """
        Rebalance instance weights based on performance.
        
        Args:
            performance_window: Time window for performance calculation (seconds)
        """
        current_time = time.time()
        
        for framework, instances in self.instances.items():
            if len(instances) <= 1:
                continue
                
            # Calculate performance scores
            performance_scores = []
            
            for instance in instances:
                # Skip if no recent data
                if current_time - instance.last_health_check > performance_window:
                    performance_scores.append(1.0)
                    continue
                    
                # Calculate performance score (higher is better)
                error_rate = instance.total_errors / max(1, instance.total_requests)
                response_score = 1.0 / max(0.1, instance.average_response_time)
                health_factor = instance.health_score
                
                score = health_factor * response_score * (1 - error_rate)
                performance_scores.append(score)
                
            # Normalize and update weights
            total_score = sum(performance_scores)
            if total_score > 0:
                for i, instance in enumerate(instances):
                    instance.weight = performance_scores[i] / total_score * len(instances)
                    
        logger.info("Rebalanced instance weights based on performance")


from typing import Callable