"""Business Rule Chain for LangChain.

This module provides a LangChain chain that evaluates business rules
and coordinates with the Business Logic Orchestrator.
"""

from typing import Any, Dict, List, Optional
from langchain.chains.base import Chain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.pydantic_v1 import Field

class BusinessRuleChain(Chain):
    """Chain for evaluating business rules within LangChain workflows."""
    
    orchestrator: Any = Field(description="Business Logic Orchestrator instance")
    rule_name: str = Field(description="Name of the business rule to evaluate")
    input_key: str = Field(default="input", description="Input key for the chain")
    output_key: str = Field(default="output", description="Output key for the chain")
    
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
        """Execute the business rule evaluation."""
        if run_manager:
            run_manager.on_text(f"Evaluating business rule: {self.rule_name}\n")
        
        # Extract input data
        input_data = inputs[self.input_key]
        
        # Evaluate business rule through orchestrator
        result = self.orchestrator.evaluate_rule(
            rule_name=self.rule_name,
            context=input_data
        )
        
        if run_manager:
            run_manager.on_text(f"Rule evaluation result: {result['decision']}\n")
        
        return {self.output_key: result}
    
    @property
    def _chain_type(self) -> str:
        """Return the chain type."""
        return "business_rule_chain"
    
    @classmethod
    def from_orchestrator(
        cls,
        orchestrator: Any,
        rule_name: str,
        **kwargs: Any
    ) -> "BusinessRuleChain":
        """Create a BusinessRuleChain from an orchestrator instance."""
        return cls(
            orchestrator=orchestrator,
            rule_name=rule_name,
            **kwargs
        )