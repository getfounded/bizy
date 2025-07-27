"""Rule Evaluation Chain for LangChain.

This module provides a LangChain chain that evaluates complex business
rules with LLM-powered decision making.
"""

from typing import Any, Dict, List, Optional
from langchain.chains.base import Chain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.pydantic_v1 import Field
from langchain.schema import BasePromptTemplate
from langchain.schema.language_model import BaseLanguageModel

class RuleEvaluationChain(Chain):
    """Chain for evaluating complex business rules with LLM assistance."""
    
    llm: BaseLanguageModel = Field(description="Language model for rule evaluation")
    prompt: BasePromptTemplate = Field(description="Prompt template for rule evaluation")
    orchestrator: Any = Field(description="Business Logic Orchestrator instance")
    rule_set: str = Field(description="Name of the rule set to evaluate")
    input_key: str = Field(default="input", description="Input key for the chain")
    output_key: str = Field(default="output", description="Output key for the chain")
    use_llm_reasoning: bool = Field(
        default=True,
        description="Whether to use LLM for complex reasoning"
    )
    
    @property
    def input_keys(self) -> List[str]:
        """Input keys for this chain."""
        return [self.input_key]
    
    @property
    def output_keys(self) -> List[str]:
        """Output keys for this chain."""
        return [self.output_key]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute rule evaluation with optional LLM reasoning."""
        if run_manager:
            run_manager.on_text(f"Evaluating rule set: {self.rule_set}\n")
        
        input_data = inputs[self.input_key]
        
        # Get applicable rules from orchestrator
        applicable_rules = self.orchestrator.get_applicable_rules(
            rule_set=self.rule_set,
            context=input_data
        )
        
        if run_manager:
            run_manager.on_text(
                f"Found {len(applicable_rules)} applicable rules\n"
            )
        
        evaluations = []
        
        for rule in applicable_rules:
            # Basic rule evaluation
            basic_result = self.orchestrator.evaluate_rule(
                rule_name=rule["name"],
                context=input_data
            )
            
            if self.use_llm_reasoning and rule.get("requires_reasoning", False):
                # Use LLM for complex reasoning
                if run_manager:
                    run_manager.on_text(
                        f"Using LLM reasoning for rule: {rule['name']}\n"
                    )
                
                # Format prompt with rule context
                prompt_value = self.prompt.format_prompt(
                    rule=rule,
                    context=input_data,
                    basic_evaluation=basic_result
                )
                
                # Get LLM reasoning
                llm_response = self.llm.generate_prompt(
                    [prompt_value],
                    callbacks=run_manager.get_child() if run_manager else None
                )
                
                reasoning = llm_response.generations[0][0].text
                
                # Combine basic evaluation with LLM reasoning
                evaluation = {
                    **basic_result,
                    "reasoning": reasoning,
                    "confidence": self._extract_confidence(reasoning)
                }
            else:
                evaluation = basic_result
            
            evaluations.append({
                "rule": rule["name"],
                "result": evaluation
            })
        
        # Aggregate evaluations
        final_decision = self._aggregate_decisions(evaluations)
        
        if run_manager:
            run_manager.on_text(
                f"Final decision: {final_decision['decision']}\n"
            )
        
        return {self.output_key: final_decision}
    
    def _extract_confidence(self, reasoning: str) -> float:
        """Extract confidence score from LLM reasoning."""
        # Simple implementation - could be enhanced
        if "high confidence" in reasoning.lower():
            return 0.9
        elif "medium confidence" in reasoning.lower():
            return 0.7
        elif "low confidence" in reasoning.lower():
            return 0.4
        return 0.6
    
    def _aggregate_decisions(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple rule evaluations into final decision."""
        decisions = [eval["result"]["decision"] for eval in evaluations]
        confidences = [
            eval["result"].get("confidence", 1.0) 
            for eval in evaluations
        ]
        
        # Weighted voting based on confidence
        decision_weights = {}
        for decision, confidence in zip(decisions, confidences):
            if decision not in decision_weights:
                decision_weights[decision] = 0
            decision_weights[decision] += confidence
        
        # Select decision with highest weight
        final_decision = max(decision_weights.items(), key=lambda x: x[1])
        
        return {
            "decision": final_decision[0],
            "confidence": final_decision[1] / sum(confidences),
            "evaluations": evaluations,
            "decision_weights": decision_weights
        }
    
    @property
    def _chain_type(self) -> str:
        """Return the chain type."""
        return "rule_evaluation_chain"