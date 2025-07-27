"""Business Process Workflow for Temporal.

This module provides Temporal workflows for orchestrating complex
business processes with rule evaluation and framework coordination.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional
from temporalio import workflow
from temporalio.workflow import ActivityOptions

from ..activities import (
    BusinessRuleActivity,
    FrameworkCoordinatorActivity,
    BusinessRuleInput,
    BusinessRuleOutput,
    FrameworkAction,
    FrameworkResult
)

@dataclass
class BusinessProcessInput:
    """Input for business process workflow."""
    process_type: str
    business_context: Dict[str, Any]
    rule_sets: List[str]
    frameworks_to_coordinate: List[str]
    process_config: Dict[str, Any]

@dataclass
class BusinessProcessOutput:
    """Output from business process workflow."""
    process_id: str
    status: str
    decisions: List[BusinessRuleOutput]
    framework_results: List[FrameworkResult]
    final_outcome: Dict[str, Any]
    execution_summary: Dict[str, Any]

@workflow.defn(name="BusinessProcessWorkflow")
class BusinessProcessWorkflow:
    """Workflow for orchestrating complex business processes."""
    
    @workflow.run
    async def run(self, input: BusinessProcessInput) -> BusinessProcessOutput:
        """Execute the business process workflow."""
        workflow.logger.info(
            f"Starting business process: {input.process_type}"
        )
        
        # Initialize activities with retry policies
        rule_activity = workflow.activity_proxy(
            BusinessRuleActivity,
            activity_options=ActivityOptions(
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3
                )
            )
        )
        
        coordinator_activity = workflow.activity_proxy(
            FrameworkCoordinatorActivity,
            activity_options=ActivityOptions(
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3
                )
            )
        )
        
        # Step 1: Validate business context
        context_valid = await rule_activity.validate_business_context(
            context=input.business_context,
            required_fields=input.process_config.get("required_fields", [])
        )
        
        if not context_valid:
            return BusinessProcessOutput(
                process_id=workflow.info().workflow_id,
                status="failed_validation",
                decisions=[],
                framework_results=[],
                final_outcome={"error": "Invalid business context"},
                execution_summary={"stage": "validation"}
            )
        
        # Step 2: Evaluate business rules
        workflow.logger.info("Evaluating business rules")
        all_decisions = []
        
        for rule_set in input.rule_sets:
            decisions = await rule_activity.evaluate_rule_set(
                rule_set=rule_set,
                context=input.business_context
            )
            all_decisions.extend(decisions)
        
        # Step 3: Aggregate decisions
        aggregation_strategy = input.process_config.get(
            "aggregation_strategy", 
            "majority"
        )
        
        final_decision = await rule_activity.aggregate_rule_decisions(
            decisions=all_decisions,
            aggregation_strategy=aggregation_strategy
        )
        
        workflow.logger.info(
            f"Business rules evaluated - Decision: {final_decision.decision}"
        )
        
        # Step 4: Check framework availability
        availability = await coordinator_activity.validate_framework_availability(
            frameworks=input.frameworks_to_coordinate
        )
        
        available_frameworks = [
            fw for fw, available in availability.items() if available
        ]
        
        if not available_frameworks:
            return BusinessProcessOutput(
                process_id=workflow.info().workflow_id,
                status="no_frameworks_available",
                decisions=all_decisions,
                framework_results=[],
                final_outcome={"error": "No frameworks available"},
                execution_summary={
                    "stage": "framework_validation",
                    "availability": availability
                }
            )
        
        # Step 5: Execute framework coordination based on decision
        framework_actions = self._generate_framework_actions(
            decision=final_decision,
            available_frameworks=available_frameworks,
            process_config=input.process_config
        )
        
        coordination_result = await coordinator_activity.coordinate_framework_sequence(
            actions=framework_actions,
            stop_on_failure=input.process_config.get("stop_on_failure", True)
        )
        
        # Step 6: Synthesize final outcome
        synthesis_result = await coordinator_activity.synthesize_framework_results(
            results=coordination_result["results"],
            synthesis_strategy=input.process_config.get(
                "synthesis_strategy",
                "merge"
            )
        )
        
        # Compile final output
        final_outcome = {
            "business_decision": final_decision.decision,
            "confidence": final_decision.confidence,
            "synthesized_data": synthesis_result["synthesized_data"],
            "process_metadata": {
                "process_type": input.process_type,
                "frameworks_used": available_frameworks,
                "total_rules_evaluated": len(all_decisions)
            }
        }
        
        workflow.logger.info("Business process completed successfully")
        
        return BusinessProcessOutput(
            process_id=workflow.info().workflow_id,
            status="completed",
            decisions=all_decisions,
            framework_results=coordination_result["results"],
            final_outcome=final_outcome,
            execution_summary={
                "stage": "completed",
                "total_execution_time_ms": coordination_result["summary"]["total_execution_time_ms"],
                "rules_evaluated": len(all_decisions),
                "frameworks_coordinated": len(available_frameworks)
            }
        )
    
    def _generate_framework_actions(
        self,
        decision: BusinessRuleOutput,
        available_frameworks: List[str],
        process_config: Dict[str, Any]
    ) -> List[FrameworkAction]:
        """Generate framework actions based on business decision."""
        actions = []
        
        # Get action mappings from config
        action_mappings = process_config.get("decision_actions", {})
        
        if decision.decision in action_mappings:
            decision_actions = action_mappings[decision.decision]
            
            for action_config in decision_actions:
                framework = action_config["framework"]
                
                # Only include if framework is available
                if framework in available_frameworks:
                    actions.append(
                        FrameworkAction(
                            framework=framework,
                            action=action_config["action"],
                            params=action_config.get("params", {}),
                            timeout_seconds=action_config.get("timeout", 30),
                            retry_count=action_config.get("retry_count", 3)
                        )
                    )
        
        # Add default actions if no specific mapping
        if not actions and process_config.get("default_actions"):
            for default_action in process_config["default_actions"]:
                framework = default_action["framework"]
                
                if framework in available_frameworks:
                    actions.append(
                        FrameworkAction(
                            framework=framework,
                            action=default_action["action"],
                            params=default_action.get("params", {}),
                            timeout_seconds=default_action.get("timeout", 30),
                            retry_count=default_action.get("retry_count", 3)
                        )
                    )
        
        return actions