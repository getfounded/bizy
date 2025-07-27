"""Business Logic Node for LangGraph.

This module provides a LangGraph node that integrates business logic
evaluation into graph-based workflows.
"""

from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph
from langchain.pydantic_v1 import BaseModel, Field

class BusinessLogicState(TypedDict):
    """State for business logic evaluation in LangGraph."""
    input_data: Dict[str, Any]
    rule_results: List[Dict[str, Any]]
    decisions: List[str]
    current_framework: Optional[str]
    execution_path: List[str]
    final_output: Optional[Dict[str, Any]]

class BusinessLogicNode(BaseModel):
    """LangGraph node for business logic evaluation."""
    
    orchestrator: Any = Field(description="Business Logic Orchestrator instance")
    node_name: str = Field(default="business_logic", description="Name of the node")
    rule_sets: List[str] = Field(description="Rule sets to evaluate")
    
    class Config:
        arbitrary_types_allowed = True
    
    def evaluate_rules(self, state: BusinessLogicState) -> BusinessLogicState:
        """Evaluate business rules based on current state."""
        input_data = state["input_data"]
        rule_results = []
        
        for rule_set in self.rule_sets:
            # Get applicable rules
            applicable_rules = self.orchestrator.get_applicable_rules(
                rule_set=rule_set,
                context=input_data
            )
            
            # Evaluate each rule
            for rule in applicable_rules:
                result = self.orchestrator.evaluate_rule(
                    rule_name=rule["name"],
                    context=input_data
                )
                
                rule_results.append({
                    "rule_set": rule_set,
                    "rule_name": rule["name"],
                    "result": result
                })
        
        # Update state with results
        state["rule_results"] = rule_results
        state["decisions"] = [r["result"]["decision"] for r in rule_results]
        state["execution_path"].append(f"{self.node_name}_evaluated")
        
        return state
    
    def route_decision(self, state: BusinessLogicState) -> str:
        """Route to next node based on rule evaluation results."""
        decisions = state["decisions"]
        
        # Routing logic based on decisions
        if all(d == "approve" for d in decisions):
            return "approved_path"
        elif any(d == "escalate" for d in decisions):
            return "escalation_path"
        elif any(d == "reject" for d in decisions):
            return "rejection_path"
        else:
            return "review_path"
    
    def create_node_functions(self) -> Dict[str, Any]:
        """Create functions for use in LangGraph."""
        return {
            "evaluate": self.evaluate_rules,
            "route": self.route_decision
        }
    
    def add_to_graph(self, graph: StateGraph) -> None:
        """Add this node to a LangGraph StateGraph."""
        graph.add_node(self.node_name, self.evaluate_rules)
        
        # Add conditional edges based on routing
        graph.add_conditional_edges(
            self.node_name,
            self.route_decision,
            {
                "approved_path": "approval_handler",
                "escalation_path": "escalation_handler",
                "rejection_path": "rejection_handler",
                "review_path": "review_handler"
            }
        )