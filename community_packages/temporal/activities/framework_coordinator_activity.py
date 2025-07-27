"""Framework Coordinator Activity for Temporal.

This module provides Temporal activities for coordinating actions
across multiple AI frameworks.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from temporalio import activity
from temporalio.exceptions import ApplicationError
import asyncio

@dataclass
class FrameworkAction:
    """Represents an action to execute on a framework."""
    framework: str
    action: str
    params: Dict[str, Any]
    timeout_seconds: int = 30
    retry_count: int = 3

@dataclass
class FrameworkResult:
    """Result from framework execution."""
    framework: str
    action: str
    success: bool
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_time_ms: int

class FrameworkCoordinatorActivity:
    """Temporal activity for cross-framework coordination."""
    
    def __init__(self, orchestrator: Any):
        """Initialize with Business Logic Orchestrator."""
        self.orchestrator = orchestrator
    
    @activity.defn(name="execute_framework_action")
    async def execute_framework_action(
        self, 
        action: FrameworkAction
    ) -> FrameworkResult:
        """Execute a single action on a specific framework."""
        activity.logger.info(
            f"Executing action '{action.action}' on framework '{action.framework}'"
        )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute through orchestrator with timeout
            result = await asyncio.wait_for(
                self.orchestrator.execute_action_async(
                    framework=action.framework,
                    action=action.action,
                    params=action.params
                ),
                timeout=action.timeout_seconds
            )
            
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            activity.logger.info(
                f"Action completed successfully in {execution_time}ms"
            )
            
            return FrameworkResult(
                framework=action.framework,
                action=action.action,
                success=True,
                result=result,
                error=None,
                execution_time_ms=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            error_msg = f"Action timed out after {action.timeout_seconds}s"
            activity.logger.error(error_msg)
            
            return FrameworkResult(
                framework=action.framework,
                action=action.action,
                success=False,
                result=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            error_msg = f"Action failed: {str(e)}"
            activity.logger.error(error_msg)
            
            return FrameworkResult(
                framework=action.framework,
                action=action.action,
                success=False,
                result=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    @activity.defn(name="execute_parallel_actions")
    async def execute_parallel_actions(
        self,
        actions: List[FrameworkAction]
    ) -> List[FrameworkResult]:
        """Execute multiple framework actions in parallel."""
        activity.logger.info(
            f"Executing {len(actions)} actions in parallel"
        )
        
        # Create tasks for parallel execution
        tasks = [
            self.execute_framework_action(action)
            for action in actions
        ]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to FrameworkResult
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    FrameworkResult(
                        framework=actions[i].framework,
                        action=actions[i].action,
                        success=False,
                        result=None,
                        error=str(result),
                        execution_time_ms=0
                    )
                )
            else:
                final_results.append(result)
        
        success_count = sum(1 for r in final_results if r.success)
        activity.logger.info(
            f"Parallel execution completed - {success_count}/{len(actions)} successful"
        )
        
        return final_results
    
    @activity.defn(name="coordinate_framework_sequence")
    async def coordinate_framework_sequence(
        self,
        actions: List[FrameworkAction],
        stop_on_failure: bool = False
    ) -> Dict[str, Any]:
        """Coordinate a sequence of framework actions with dependencies."""
        activity.logger.info(
            f"Coordinating sequence of {len(actions)} actions"
        )
        
        results = []
        context = {}
        
        for i, action in enumerate(actions):
            activity.logger.info(
                f"Executing step {i+1}/{len(actions)}: "
                f"{action.framework}.{action.action}"
            )
            
            # Add context from previous results
            enriched_params = {
                **action.params,
                "context": context,
                "step_number": i + 1
            }
            
            enriched_action = FrameworkAction(
                framework=action.framework,
                action=action.action,
                params=enriched_params,
                timeout_seconds=action.timeout_seconds,
                retry_count=action.retry_count
            )
            
            result = await self.execute_framework_action(enriched_action)
            results.append(result)
            
            if result.success and result.result:
                # Update context with successful results
                context[f"{action.framework}_{action.action}"] = result.result
            elif stop_on_failure and not result.success:
                activity.logger.warning(
                    f"Stopping sequence due to failure at step {i+1}"
                )
                break
        
        # Compile final result
        successful_steps = sum(1 for r in results if r.success)
        total_execution_time = sum(r.execution_time_ms for r in results)
        
        activity.logger.info(
            f"Sequence completed - {successful_steps}/{len(results)} successful, "
            f"Total time: {total_execution_time}ms"
        )
        
        return {
            "results": results,
            "context": context,
            "summary": {
                "total_steps": len(results),
                "successful_steps": successful_steps,
                "failed_steps": len(results) - successful_steps,
                "total_execution_time_ms": total_execution_time,
                "stopped_early": stop_on_failure and successful_steps < len(actions)
            }
        }
    
    @activity.defn(name="validate_framework_availability")
    async def validate_framework_availability(
        self,
        frameworks: List[str]
    ) -> Dict[str, bool]:
        """Check if frameworks are available and healthy."""
        activity.logger.info(
            f"Validating availability of {len(frameworks)} frameworks"
        )
        
        availability = {}
        
        for framework in frameworks:
            try:
                is_available = await self.orchestrator.check_framework_health(framework)
                availability[framework] = is_available
                
                activity.logger.info(
                    f"Framework '{framework}' is {'available' if is_available else 'unavailable'}"
                )
            except Exception as e:
                activity.logger.error(
                    f"Error checking framework '{framework}': {str(e)}"
                )
                availability[framework] = False
        
        available_count = sum(1 for v in availability.values() if v)
        activity.logger.info(
            f"Validation complete - {available_count}/{len(frameworks)} available"
        )
        
        return availability
    
    @activity.defn(name="synthesize_framework_results")
    async def synthesize_framework_results(
        self,
        results: List[FrameworkResult],
        synthesis_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """Synthesize results from multiple framework executions."""
        activity.logger.info(
            f"Synthesizing {len(results)} results using strategy: {synthesis_strategy}"
        )
        
        if synthesis_strategy == "merge":
            # Merge all successful results
            synthesized = {}
            for result in results:
                if result.success and result.result:
                    synthesized[f"{result.framework}_{result.action}"] = result.result
            
        elif synthesis_strategy == "first_success":
            # Return first successful result
            for result in results:
                if result.success and result.result:
                    synthesized = result.result
                    break
            else:
                synthesized = {}
                
        elif synthesis_strategy == "aggregate":
            # Aggregate results by framework
            synthesized = {}
            for result in results:
                if result.framework not in synthesized:
                    synthesized[result.framework] = []
                
                synthesized[result.framework].append({
                    "action": result.action,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error
                })
                
        else:
            raise ApplicationError(
                f"Unknown synthesis strategy: {synthesis_strategy}",
                non_retryable=True
            )
        
        activity.logger.info("Synthesis completed")
        
        return {
            "synthesized_data": synthesized,
            "synthesis_metadata": {
                "strategy": synthesis_strategy,
                "total_results": len(results),
                "successful_results": sum(1 for r in results if r.success),
                "frameworks_involved": list(set(r.framework for r in results))
            }
        }