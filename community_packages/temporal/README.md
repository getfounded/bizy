# Bizy Temporal Integration

Production-ready Temporal activities and workflows powered by Bizy for business process automation with AI agent coordination.

## Overview

This package provides Temporal-native components for:

- **Business Rule Activities**: Evaluate complex business rules within workflows
- **Framework Coordination**: Orchestrate actions across multiple AI frameworks
- **Error Handling Patterns**: Robust error recovery for AI operations
- **Monitoring Integration**: Built-in observability for business metrics

## Features

### 📋 Business Rule Activities
Evaluate business rules as Temporal activities:

```python
from bizy_temporal.activities import BusinessRuleActivity

rule_activity = BusinessRuleActivity(orchestrator)

# In your workflow
decision = await workflow.execute_activity(
    rule_activity.evaluate_business_rule,
    BusinessRuleInput(
        rule_name="credit_approval",
        context={"amount": 50000, "credit_score": 750}
    )
)
```

### 🔄 Cross-Framework Coordination
Coordinate AI frameworks within workflows:

```python
from bizy_temporal.activities import FrameworkCoordinatorActivity

coordinator = FrameworkCoordinatorActivity(orchestrator)

# Execute actions across frameworks
results = await workflow.execute_activity(
    coordinator.execute_parallel_actions,
    [
        FrameworkAction("langchain", "analyze", params),
        FrameworkAction("mcp", "fetch_data", params),
        FrameworkAction("semantic_kernel", "generate", params)
    ]
)
```

### 🎯 Business Process Workflows
Complete workflows for business automation:

```python
from bizy_temporal.workflows import BusinessProcessWorkflow

# Start a business process
handle = await client.start_workflow(
    BusinessProcessWorkflow.run,
    BusinessProcessInput(
        process_type="loan_approval",
        rule_sets=["credit_rules", "risk_assessment"],
        frameworks_to_coordinate=["langchain", "temporal", "mcp"]
    )
)
```

## Installation

```bash
pip install bizy-temporal
```

## Quick Start

### 1. Define Business Activities

```python
from temporalio.worker import Worker
from bizy_temporal.activities import BusinessRuleActivity, FrameworkCoordinatorActivity

# Initialize activities
rule_activity = BusinessRuleActivity(orchestrator)
coordinator_activity = FrameworkCoordinatorActivity(orchestrator)

# Create worker with activities
worker = Worker(
    client,
    task_queue="business-logic-queue",
    activities=[
        rule_activity.evaluate_business_rule,
        rule_activity.evaluate_rule_set,
        coordinator_activity.execute_framework_action,
        coordinator_activity.execute_parallel_actions
    ]
)
```

### 2. Create Business Workflows

```python
@workflow.defn
class LoanApprovalWorkflow:
    @workflow.run
    async def run(self, input: LoanApplicationInput) -> LoanDecision:
        # Validate application
        validation = await workflow.execute_activity(
            validate_application,
            input.application_data
        )
        
        # Evaluate business rules
        credit_decision = await workflow.execute_activity(
            rule_activity.evaluate_business_rule,
            BusinessRuleInput(
                rule_name="credit_check",
                context=validation.credit_data
            )
        )
        
        # Coordinate AI analysis
        if credit_decision.decision == "review_required":
            ai_results = await workflow.execute_activity(
                coordinator_activity.coordinate_framework_sequence,
                [
                    FrameworkAction("langchain", "analyze_documents"),
                    FrameworkAction("mcp", "verify_employment"),
                    FrameworkAction("ml_model", "predict_default_risk")
                ]
            )
        
        return LoanDecision(approved=True, terms=terms)
```

### 3. Handle Errors Gracefully

```python
from bizy_temporal.workflows import ErrorHandlingWorkflow

@workflow.defn
class RobustAIWorkflow:
    @workflow.run
    async def run(self, input: WorkflowInput) -> WorkflowOutput:
        # Execute with retry and compensation
        try:
            result = await workflow.execute_activity(
                ai_activity,
                input,
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    backoff_coefficient=2.0
                )
            )
        except ActivityError as e:
            # Execute compensation logic
            await workflow.execute_activity(
                compensation_activity,
                CompensationInput(
                    failed_activity="ai_activity",
                    error=str(e)
                )
            )
```

## Activity Patterns

### Business Rule Evaluation
```python
# Single rule evaluation
result = await workflow.execute_activity(
    rule_activity.evaluate_business_rule,
    BusinessRuleInput(rule_name="kyc_check", context=customer_data)
)

# Rule set evaluation
results = await workflow.execute_activity(
    rule_activity.evaluate_rule_set,
    rule_set="compliance_rules",
    context=transaction_data
)

# Aggregate decisions
final_decision = await workflow.execute_activity(
    rule_activity.aggregate_rule_decisions,
    decisions=results,
    aggregation_strategy="weighted"
)
```

### Framework Coordination
```python
# Sequential execution
sequence_result = await workflow.execute_activity(
    coordinator.coordinate_framework_sequence,
    actions=[...],
    stop_on_failure=True
)

# Parallel execution
parallel_results = await workflow.execute_activity(
    coordinator.execute_parallel_actions,
    actions=[...]
)

# Result synthesis
synthesized = await workflow.execute_activity(
    coordinator.synthesize_framework_results,
    results=parallel_results,
    synthesis_strategy="merge"
)
```

## Error Handling

Built-in patterns for robust error handling:

1. **Retry with Backoff**: Automatic retry for transient failures
2. **Circuit Breaker**: Prevent cascading failures
3. **Compensation**: Rollback actions on failure
4. **Dead Letter Queue**: Handle permanently failed activities

## Monitoring & Observability

Activities include built-in metrics:

- Rule evaluation latency
- Framework coordination success rates
- Business decision distribution
- Error rates by activity type

## Examples

See the `examples/` directory for complete workflows:

- `loan_approval_workflow.py`: Multi-stage loan approval
- `customer_service_workflow.py`: AI-powered customer service
- `fraud_detection_workflow.py`: Real-time fraud detection

## Best Practices

1. **Idempotency**: All activities are idempotent by design
2. **Timeouts**: Configure appropriate timeouts for AI operations
3. **Versioning**: Use Temporal's versioning for workflow updates
4. **Testing**: Comprehensive test helpers included

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [https://docs.bizy.work](https://docs.bizy.work)
- Issues: [GitHub Issues](https://github.com/getfounded/bizy/issues)
- Discussions: [GitHub Discussions](https://github.com/getfounded/bizy/discussions)