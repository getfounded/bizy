---
sidebar_position: 3
---

# Your First Workflow

Build a complete customer service workflow using multiple AI frameworks.

## Overview

We'll create a workflow that:
1. Analyzes customer sentiment (LangChain)
2. Checks customer history (Zep Memory)
3. Creates support ticket (MCP Tools)
4. Starts resolution workflow (Temporal)

## Step 1: Define the Business Rules

Create `rules/customer_service.yaml`:

```yaml
rule_set: customer_service
rules:
  - rule: analyze_sentiment
    description: Analyze customer message sentiment
    priority: high
    conditions:
      - message.text != null
    actions:
      - framework: langchain
        action: sentiment_analysis
        output: sentiment_score

  - rule: check_escalation
    description: Determine if escalation needed
    priority: high
    conditions:
      - sentiment_score < 0.3
      - customer.tier == "premium"
    actions:
      - framework: zep
        action: get_customer_history
      - framework: temporal
        action: start_escalation_workflow
        params:
          priority: high

  - rule: create_ticket
    description: Create support ticket
    priority: medium
    conditions:
      - sentiment_score < 0.7
    actions:
      - framework: mcp
        action: create_ticket
        params:
          type: support
          auto_assign: true
```

## Step 2: Initialize the Frameworks

```python
from bizy.core import MetaOrchestrator
from bizy.adapters import (
    LangChainAdapter,
    TemporalAdapter,
    MCPAdapter,
    ZepAdapter
)

async def setup_orchestrator():
    orchestrator = MetaOrchestrator()
    
    # Configure adapters
    adapters = {
        "langchain": LangChainAdapter({"api_key": "..."}),
        "temporal": TemporalAdapter({"host": "localhost"}),
        "mcp": MCPAdapter({"server_url": "http://localhost:8080"}),
        "zep": ZepAdapter({"api_url": "http://localhost:8000"})
    }
    
    # Register all adapters
    for name, adapter in adapters.items():
        await adapter.connect()
        orchestrator.register_adapter(name, adapter)
    
    # Load rules
    orchestrator.load_rules("rules/customer_service.yaml")
    
    return orchestrator
```

## Step 3: Create the Workflow Handler

```python
class CustomerServiceHandler:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    async def handle_customer_message(self, customer_id: str, message: str):
        # Prepare context
        context = {
            "customer": await self.get_customer_info(customer_id),
            "message": {"text": message}
        }
        
        # Execute rules
        result = await self.orchestrator.execute(
            rule_set="customer_service",
            context=context
        )
        
        return {
            "ticket_id": result.get("ticket_id"),
            "workflow_id": result.get("workflow_id"),
            "sentiment": result.get("sentiment_score"),
            "actions_taken": result.get("executed_actions")
        }
```

## Step 4: Run the Workflow

```python
async def main():
    # Setup
    orchestrator = await setup_orchestrator()
    handler = CustomerServiceHandler(orchestrator)
    
    # Handle a customer message
    result = await handler.handle_customer_message(
        customer_id="cust_123",
        message="I'm very frustrated with the service!"
    )
    
    print(f"Ticket created: {result['ticket_id']}")
    print(f"Sentiment score: {result['sentiment']}")
    print(f"Actions taken: {result['actions_taken']}")

# Run
import asyncio
asyncio.run(main())
```

## Expected Output

```
Ticket created: TICK-2024-001
Sentiment score: 0.2
Actions taken: [
    "langchain.sentiment_analysis",
    "zep.get_customer_history", 
    "temporal.start_escalation_workflow",
    "mcp.create_ticket"
]
```

## Next Steps

- Add error handling and retries
- Implement custom actions
- Create workflow monitoring
- Scale with multiple workers

## Learn More

- [Business Rule Patterns](../rules/best-practices)
- [Error Handling](../tutorials/error-handling)
- [Production Deployment](../deployment/requirements)