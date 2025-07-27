"""Business Rule Activity for Temporal.

This module provides Temporal activities for evaluating business rules
within workflow executions.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from temporalio import activity
from temporalio.exceptions import ApplicationError

@dataclass
class BusinessRuleInput:
    """Input for business rule evaluation activity."""
    rule_name: str
    context: Dict[str, Any]
    rule_set: Optional[str] = None
    evaluation_mode: str = "strict"  # strict, lenient, advisory

@dataclass
class BusinessRuleOutput:
    """Output from business rule evaluation activity."""
    decision: str
    confidence: float
    reasons: List[str]
    applied_rules: List[str]
    metadata: Dict[str, Any]

class BusinessRuleActivity:
    """Temporal activity for business rule evaluation."""
    
    def __init__(self, orchestrator: Any):
        """Initialize with Business Logic Orchestrator."""
        self.orchestrator = orchestrator
    
    @activity.defn(name="evaluate_business_rule")
    async def evaluate_business_rule(self, input: BusinessRuleInput) -> BusinessRuleOutput:
        """Evaluate a business rule within a Temporal workflow."""
        activity.logger.info(
            f"Evaluating business rule: {input.rule_name} "
            f"with mode: {input.evaluation_mode}"
        )
        
        try:
            # Evaluate the rule through orchestrator
            result = await self.orchestrator.evaluate_rule_async(
                rule_name=input.rule_name,
                context=input.context,
                mode=input.evaluation_mode
            )
            
            # Extract decision components
            decision = result.get("decision", "no_decision")
            confidence = result.get("confidence", 0.0)
            reasons = result.get("reasons", [])
            
            # Log decision for audit
            activity.logger.info(
                f"Rule evaluation completed - Decision: {decision}, "
                f"Confidence: {confidence}"
            )
            
            return BusinessRuleOutput(
                decision=decision,
                confidence=confidence,
                reasons=reasons,
                applied_rules=[input.rule_name],
                metadata={
                    "evaluation_mode": input.evaluation_mode,
                    "rule_version": result.get("version", "1.0"),
                    "execution_time_ms": result.get("execution_time", 0)
                }
            )
            
        except Exception as e:
            activity.logger.error(f"Error evaluating rule: {str(e)}")
            raise ApplicationError(
                f"Failed to evaluate business rule: {input.rule_name}",
                non_retryable=False
            )
    
    @activity.defn(name="evaluate_rule_set")
    async def evaluate_rule_set(
        self, 
        rule_set: str, 
        context: Dict[str, Any]
    ) -> List[BusinessRuleOutput]:
        """Evaluate a complete set of business rules."""
        activity.logger.info(f"Evaluating rule set: {rule_set}")
        
        try:
            # Get all rules in the set
            rules = await self.orchestrator.get_rule_set(rule_set)
            
            # Evaluate each rule
            results = []
            for rule in rules:
                input = BusinessRuleInput(
                    rule_name=rule["name"],
                    context=context,
                    rule_set=rule_set
                )
                
                result = await self.evaluate_business_rule(input)
                results.append(result)
            
            activity.logger.info(
                f"Rule set evaluation completed - {len(results)} rules evaluated"
            )
            
            return results
            
        except Exception as e:
            activity.logger.error(f"Error evaluating rule set: {str(e)}")
            raise ApplicationError(
                f"Failed to evaluate rule set: {rule_set}",
                non_retryable=False
            )
    
    @activity.defn(name="validate_business_context")
    async def validate_business_context(
        self, 
        context: Dict[str, Any],
        required_fields: List[str]
    ) -> bool:
        """Validate that context contains required fields for rule evaluation."""
        activity.logger.info("Validating business context")
        
        missing_fields = []
        for field in required_fields:
            if field not in context:
                missing_fields.append(field)
        
        if missing_fields:
            activity.logger.warning(
                f"Context validation failed - Missing fields: {missing_fields}"
            )
            return False
        
        activity.logger.info("Context validation successful")
        return True
    
    @activity.defn(name="aggregate_rule_decisions")
    async def aggregate_rule_decisions(
        self,
        decisions: List[BusinessRuleOutput],
        aggregation_strategy: str = "unanimous"
    ) -> BusinessRuleOutput:
        """Aggregate multiple rule decisions into a final decision."""
        activity.logger.info(
            f"Aggregating {len(decisions)} decisions "
            f"using strategy: {aggregation_strategy}"
        )
        
        if not decisions:
            raise ApplicationError("No decisions to aggregate", non_retryable=True)
        
        # Implement different aggregation strategies
        if aggregation_strategy == "unanimous":
            # All rules must agree
            first_decision = decisions[0].decision
            if all(d.decision == first_decision for d in decisions):
                final_decision = first_decision
                confidence = min(d.confidence for d in decisions)
            else:
                final_decision = "conflict"
                confidence = 0.0
                
        elif aggregation_strategy == "majority":
            # Majority vote
            decision_counts = {}
            total_confidence = {}
            
            for d in decisions:
                decision_counts[d.decision] = decision_counts.get(d.decision, 0) + 1
                total_confidence[d.decision] = total_confidence.get(d.decision, 0) + d.confidence
            
            final_decision = max(decision_counts.items(), key=lambda x: x[1])[0]
            confidence = total_confidence[final_decision] / decision_counts[final_decision]
            
        elif aggregation_strategy == "weighted":
            # Weighted by confidence
            weighted_decisions = {}
            
            for d in decisions:
                weighted_decisions[d.decision] = weighted_decisions.get(d.decision, 0) + d.confidence
            
            final_decision = max(weighted_decisions.items(), key=lambda x: x[1])[0]
            confidence = weighted_decisions[final_decision] / sum(d.confidence for d in decisions)
            
        else:
            raise ApplicationError(
                f"Unknown aggregation strategy: {aggregation_strategy}",
                non_retryable=True
            )
        
        # Combine all reasons
        all_reasons = []
        all_rules = []
        for d in decisions:
            all_reasons.extend(d.reasons)
            all_rules.extend(d.applied_rules)
        
        activity.logger.info(
            f"Aggregation completed - Final decision: {final_decision}, "
            f"Confidence: {confidence}"
        )
        
        return BusinessRuleOutput(
            decision=final_decision,
            confidence=confidence,
            reasons=all_reasons,
            applied_rules=all_rules,
            metadata={
                "aggregation_strategy": aggregation_strategy,
                "total_rules_evaluated": len(decisions),
                "decision_distribution": decision_counts if aggregation_strategy == "majority" else {}
            }
        )