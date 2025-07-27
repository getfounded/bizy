"""Framework Coordinator Node for LangGraph.

This module provides a LangGraph node that coordinates actions
across multiple AI frameworks within graph workflows.
"""

from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph
from langchain.pydantic_v1 import BaseModel, Field
import asyncio

class CoordinationState(TypedDict):
    """State for cross-framework coordination in LangGraph."""
    input_data: Dict[str, Any]
    framework_results: Dict[str, Any]
    coordination_plan: List[Dict[str, Any]]
    execution_status: Dict[str, str]
    synthesized_output: Optional[Dict[str, Any]]
    errors: List[Dict[str, Any]]

class FrameworkCoordinatorNode(BaseModel):
    """LangGraph node for coordinating across AI frameworks."""
    
    orchestrator: Any = Field(description="Business Logic Orchestrator instance")
    node_name: str = Field(default="framework_coordinator", description="Node name")
    frameworks: List[str] = Field(description="Frameworks to coordinate")
    coordination_strategy: str = Field(
        default="sequential",
        description="Coordination strategy: sequential, parallel, or adaptive"
    )
    
    class Config:
        arbitrary_types_allowed = True
    
    def plan_coordination(self, state: CoordinationState) -> CoordinationState:
        """Plan the coordination strategy based on input."""
        input_data = state["input_data"]
        
        # Generate coordination plan based on input and strategy
        if self.coordination_strategy == "adaptive":
            # Use orchestrator to determine optimal plan
            plan = self.orchestrator.generate_coordination_plan(
                input_data=input_data,
                available_frameworks=self.frameworks
            )
        else:
            # Use predefined strategy
            plan = self._generate_static_plan(input_data)
        
        state["coordination_plan"] = plan
        state["execution_status"] = {
            step["id"]: "pending" for step in plan
        }
        
        return state
    
    def execute_coordination(self, state: CoordinationState) -> CoordinationState:
        """Execute the coordination plan across frameworks."""
        plan = state["coordination_plan"]
        results = {}
        
        if self.coordination_strategy == "parallel":
            # Execute in parallel
            results = self._execute_parallel(plan, state["input_data"])
        else:
            # Execute sequentially
            results = self._execute_sequential(plan, state["input_data"])
        
        state["framework_results"] = results
        
        # Update execution status
        for step_id in state["execution_status"]:
            if step_id in results:
                state["execution_status"][step_id] = "completed"
            else:
                state["execution_status"][step_id] = "failed"
        
        return state
    
    def synthesize_results(self, state: CoordinationState) -> CoordinationState:
        """Synthesize results from multiple frameworks."""
        framework_results = state["framework_results"]
        
        # Use orchestrator to synthesize
        synthesized = self.orchestrator.synthesize_results(
            results=framework_results,
            coordination_plan=state["coordination_plan"]
        )
        
        state["synthesized_output"] = synthesized
        
        return state
    
    def _generate_static_plan(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a static coordination plan."""
        plan = []
        
        for i, framework in enumerate(self.frameworks):
            plan.append({
                "id": f"step_{i}",
                "framework": framework,
                "action": "process",
                "params": {"input": input_data},
                "dependencies": [f"step_{i-1}"] if i > 0 else []
            })
        
        return plan
    
    def _execute_sequential(
        self, 
        plan: List[Dict[str, Any]], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute coordination plan sequentially."""
        results = {}
        context = input_data.copy()
        
        for step in plan:
            try:
                result = self.orchestrator.execute_action(
                    framework=step["framework"],
                    action=step["action"],
                    params={**step["params"], "context": context},
                    context=context
                )
                
                results[step["id"]] = result
                
                # Update context with results
                if step.get("update_context", True):
                    context.update(result)
                    
            except Exception as e:
                results[step["id"]] = {"error": str(e)}
        
        return results
    
    def _execute_parallel(
        self, 
        plan: List[Dict[str, Any]], 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute coordination plan in parallel."""
        # Group steps by dependencies
        dependency_groups = self._group_by_dependencies(plan)
        results = {}
        
        for group in dependency_groups:
            # Execute group in parallel
            group_results = asyncio.run(
                self._execute_group_async(group, input_data, results)
            )
            results.update(group_results)
        
        return results
    
    async def _execute_group_async(
        self,
        group: List[Dict[str, Any]],
        input_data: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a group of steps asynchronously."""
        tasks = []
        
        for step in group:
            # Build context from previous results
            context = input_data.copy()
            for dep in step.get("dependencies", []):
                if dep in previous_results:
                    context.update(previous_results[dep])
            
            task = self._execute_step_async(step, context)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return {
            step["id"]: result 
            for step, result in zip(group, results)
        }
    
    async def _execute_step_async(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single step asynchronously."""
        try:
            result = await self.orchestrator.execute_action_async(
                framework=step["framework"],
                action=step["action"],
                params={**step["params"], "context": context},
                context=context
            )
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _group_by_dependencies(
        self, 
        plan: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group steps by their dependencies for parallel execution."""
        groups = []
        processed = set()
        
        while len(processed) < len(plan):
            current_group = []
            
            for step in plan:
                if step["id"] in processed:
                    continue
                
                # Check if all dependencies are processed
                deps = step.get("dependencies", [])
                if all(dep in processed for dep in deps):
                    current_group.append(step)
            
            if current_group:
                groups.append(current_group)
                for step in current_group:
                    processed.add(step["id"])
            else:
                # Circular dependency or error
                break
        
        return groups
    
    def route_on_success(self, state: CoordinationState) -> str:
        """Route based on coordination success."""
        errors = [
            result.get("error") 
            for result in state["framework_results"].values()
            if "error" in result
        ]
        
        if errors:
            state["errors"] = errors
            return "error_handler"
        else:
            return "success_handler"
    
    def add_to_graph(self, graph: StateGraph) -> None:
        """Add this node to a LangGraph StateGraph."""
        # Add planning node
        graph.add_node(f"{self.node_name}_plan", self.plan_coordination)
        
        # Add execution node
        graph.add_node(f"{self.node_name}_execute", self.execute_coordination)
        
        # Add synthesis node
        graph.add_node(f"{self.node_name}_synthesize", self.synthesize_results)
        
        # Add edges
        graph.add_edge(f"{self.node_name}_plan", f"{self.node_name}_execute")
        graph.add_edge(f"{self.node_name}_execute", f"{self.node_name}_synthesize")
        
        # Add conditional routing
        graph.add_conditional_edges(
            f"{self.node_name}_synthesize",
            self.route_on_success,
            {
                "success_handler": "success",
                "error_handler": "error"
            }
        )