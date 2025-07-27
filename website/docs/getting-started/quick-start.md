---
sidebar_position: 2
---

# Quick Start

Build your first cross-framework workflow in 5 minutes.

## Basic Example

### 1. Define a Business Rule

Create a YAML file `rules/hello_world.yaml`:

```yaml
rule: hello_world
description: Simple greeting rule
priority: high
conditions:
  - input.name != null
actions:
  - framework: langchain
    action: generate_greeting
    params:
      template: "Hello, {name}!"
```

### 2. Create the Orchestrator

```python
from bizy.core import MetaOrchestrator
from bizy.adapters import LangChainAdapter

# Initialize orchestrator
orchestrator = MetaOrchestrator()

# Register LangChain adapter
langchain = LangChainAdapter({
    "api_key": "your-api-key"
})
orchestrator.register_adapter("langchain", langchain)

# Load business rules
orchestrator.load_rules("rules/hello_world.yaml")
```

### 3. Execute the Rule

```python
# Execute business rule
result = await orchestrator.execute(
    rule_name="hello_world",
    context={"name": "Alice"}
)

print(result)
# Output: {"greeting": "Hello, Alice!"}
```

## Multi-Framework Example

Coordinate between LangChain and Temporal:

```python
from bizy.adapters import TemporalAdapter

# Add Temporal adapter
temporal = TemporalAdapter({
    "host": "localhost",
    "port": 7233
})
orchestrator.register_adapter("temporal", temporal)

# Define multi-framework rule
rule = """
rule: process_document
conditions:
  - document.type == "invoice"
actions:
  - framework: langchain
    action: extract_data
  - framework: temporal
    action: start_approval_workflow
    params:
      workflow: "invoice_approval"
"""

# Execute
result = await orchestrator.execute(
    rule_name="process_document",
    context={"document": {"type": "invoice", "content": "..."}}
)
```

## What's Next?

- Learn about [Business Rules](../rules/rule-syntax)
- Explore [Framework Adapters](../adapters/langchain)
- Build complex [Multi-Framework Scenarios](../tutorials/multi-framework-scenarios)