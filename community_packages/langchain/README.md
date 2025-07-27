# Bizy LangChain Integration

A comprehensive integration package that brings Bizy's enterprise-grade business logic orchestration to LangChain workflows.

## Overview

This package extends LangChain with powerful business logic capabilities, enabling:

- **Business Rule Chains**: Evaluate complex business rules within LangChain workflows
- **Cross-Framework Coordination**: Seamlessly coordinate actions across multiple AI frameworks
- **LangGraph Integration**: Build graph-based workflows with business logic nodes
- **Enterprise Patterns**: Production-ready patterns for business automation

## Features

### 🔗 Business Rule Chain
Integrate business rule evaluation directly into your LangChain pipelines:

```python
from bizy_langchain import BusinessRuleChain

rule_chain = BusinessRuleChain.from_orchestrator(
    orchestrator=orchestrator,
    rule_name="customer_escalation"
)

result = rule_chain.run({"customer_tier": "premium", "sentiment": 0.2})
```

### 🌐 Cross-Framework Chain
Coordinate actions across multiple AI frameworks:

```python
from bizy_langchain import CrossFrameworkChain

cross_chain = CrossFrameworkChain.from_config(
    orchestrator=orchestrator,
    config={
        "frameworks": ["langchain", "temporal", "mcp"],
        "action_sequence": [...]
    }
)
```

### 📊 LangGraph Nodes
Build complex workflows with business logic coordination:

```python
from bizy_langchain.langgraph import BusinessLogicNode, FrameworkCoordinatorNode

logic_node = BusinessLogicNode(
    orchestrator=orchestrator,
    rule_sets=["fraud_detection", "risk_assessment"]
)

graph = StateGraph(BusinessLogicState)
logic_node.add_to_graph(graph)
```

## Installation

```bash
pip install bizy-langchain
```

## Quick Start

```python
from langchain.llms import OpenAI
from bizy_langchain import RuleEvaluationChain
from bizy.core import MetaOrchestrator

# Initialize LLM and orchestrator
llm = OpenAI()
orchestrator = MetaOrchestrator()

# Create evaluation chain
eval_chain = RuleEvaluationChain(
    llm=llm,
    orchestrator=orchestrator,
    rule_set="customer_service",
    use_llm_reasoning=True
)

# Evaluate business rules
result = eval_chain.run({
    "customer_data": {...},
    "context": {...}
})
```

## Use Cases

### Customer Service Automation
```python
# Automatically escalate based on business rules
escalation_workflow = create_customer_service_workflow()
response = escalation_workflow.run(customer_interaction)
```

### Fraud Detection Pipeline
```python
# Combine rule evaluation with LLM analysis
fraud_pipeline = create_fraud_detection_pipeline()
risk_score = fraud_pipeline.run(transaction_data)
```

### Document Processing Workflow
```python
# Coordinate document analysis across frameworks
doc_workflow = create_document_workflow()
processed = doc_workflow.run(document)
```

## Architecture

The package follows LangChain's design principles while adding:

1. **Adapter Pattern**: Clean integration with external frameworks
2. **Event-Driven Coordination**: Async communication between components
3. **Rule Engine Integration**: YAML-based business rule definitions
4. **State Management**: Consistent state handling across chains

## Examples

See the `examples/` directory for complete working examples:

- `business_logic_demo.py`: Basic integration patterns
- `langgraph_workflow.py`: Graph-based workflow examples
- `multi_framework_coordination.py`: Cross-framework scenarios

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [https://docs.bizy.work](https://docs.bizy.work)
- Issues: [GitHub Issues](https://github.com/getfounded/bizy/issues)
- Discussions: [GitHub Discussions](https://github.com/getfounded/bizy/discussions)