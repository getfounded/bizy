"""Cross-Framework Chain for LangChain.

This module provides a LangChain chain that coordinates actions
across multiple AI frameworks through the Business Logic Orchestrator.
"""

from typing import Any, Dict, List, Optional
from langchain.chains.base import Chain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.pydantic_v1 import Field, validator

class CrossFrameworkChain(Chain):
    """Chain for coordinating actions across multiple AI frameworks."""
    
    orchestrator: Any = Field(description="Business Logic Orchestrator instance")
    frameworks: List[str] = Field(description="List of frameworks to coordinate")
    action_sequence: List[Dict[str, Any]] = Field(
        description="Sequence of actions to execute across frameworks"
    )
    input_key: str = Field(default="input", description="Input key for the chain")
    output_key: str = Field(default="output", description="Output key for the chain")
    parallel_execution: bool = Field(
        default=False,
        description="Whether to execute framework actions in parallel"
    )
    
    @validator("frameworks")
    def validate_frameworks(cls, v: List[str]) -> List[str]:
        """Validate that at least one framework is specified."""
        if not v:
            raise ValueError("At least one framework must be specified")
        return v
    
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
        """Execute cross-framework coordination."""
        if run_manager:
            run_manager.on_text(
                f"Coordinating across frameworks: {', '.join(self.frameworks)}\n"
            )
        
        input_data = inputs[self.input_key]
        results = []
        
        if self.parallel_execution:
            # Execute actions in parallel across frameworks
            if run_manager:
                run_manager.on_text("Executing actions in parallel...\n")
            
            results = self.orchestrator.execute_parallel(
                action_sequence=self.action_sequence,
                context=input_data
            )
        else:
            # Execute actions sequentially
            for i, action in enumerate(self.action_sequence):
                if run_manager:
                    run_manager.on_text(
                        f"Step {i+1}: {action['framework']} - {action['action']}\n"
                    )
                
                result = self.orchestrator.execute_action(
                    framework=action["framework"],
                    action=action["action"],
                    params=action.get("params", {}),
                    context={**input_data, "previous_results": results}
                )
                
                results.append(result)
                
                # Update context with intermediate results
                if action.get("update_context", False):
                    input_data.update(result)
        
        # Synthesize results
        final_result = self.orchestrator.synthesize_results(results)
        
        if run_manager:
            run_manager.on_text(f"Cross-framework execution complete\n")
        
        return {self.output_key: final_result}
    
    @property
    def _chain_type(self) -> str:
        """Return the chain type."""
        return "cross_framework_chain"
    
    @classmethod
    def from_config(
        cls,
        orchestrator: Any,
        config: Dict[str, Any],
        **kwargs: Any
    ) -> "CrossFrameworkChain":
        """Create a CrossFrameworkChain from configuration."""
        return cls(
            orchestrator=orchestrator,
            frameworks=config["frameworks"],
            action_sequence=config["action_sequence"],
            parallel_execution=config.get("parallel_execution", False),
            **kwargs
        )