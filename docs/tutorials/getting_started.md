# Getting Started with Business Logic Orchestration

This tutorial will walk you through setting up and using the Business Logic Orchestration Layer to coordinate AI frameworks with enterprise business rules.

## Prerequisites

- Python 3.12 or higher
- Redis (for event coordination)
- Access to AI framework APIs (LangChain, Temporal, MCP, etc.)

## Installation

```bash
# Clone the repository
git clone https://github.com/business-logic-orchestrator/orchestrator.git
cd orchestrator

# Install with Poetry
poetry install

# Or with pip
pip install business-logic-orchestrator
```

## Quick Start

### 1. Initialize the Orchestrator

```python
from business_logic_orchestrator import MetaOrchestrator
from business_logic_orchestrator.adapters import LangChainAdapter, MCPAdapter

# Create orchestrator instance
orchestrator = MetaOrchestrator()

# Register framework adapters
orchestrator.register_adapter("langchain", LangChainAdapter())
orchestrator.register_adapter("mcp", MCPAdapter())
```

### 2. Define Business Rules

Create a file `rules/customer_service.yaml`:

```yaml
rules:
  - name: premium_escalation
    description: Escalate premium customer issues
    conditions:
      - customer_tier == "premium"
      - sentiment_score < 0.5
    actions:
      - framework: langchain
        action: analyze_detailed_sentiment
      - framework: temporal
        action: create_escalation_ticket
    priority: 10

  - name: standard_response
    description: Standard customer response
    conditions:
      - customer_tier == "standard"
      - sentiment_score >= 0.5
    actions:
      - framework: langchain
        action: generate_response
    priority: 5
```

### 3. Load and Execute Rules

```python
# Load rules
orchestrator.load_rules("rules/customer_service.yaml")

# Execute with context
context = {
    "customer_tier": "premium",
    "sentiment_score": 0.3,
    "message": "I'm very frustrated with the service"
}

result = orchestrator.evaluate_and_execute(
    rule_set="customer_service",
    context=context
)

print(f"Executed actions: {result['executed_actions']}")
print(f"Results: {result['framework_results']}")
```

## Core Concepts

### Business Rules

Business rules consist of:
- **Conditions**: When the rule should apply
- **Actions**: What frameworks to invoke
- **Priority**: Order of evaluation

### Framework Adapters

Each adapter provides:
- Connection management
- Action execution
- Error handling
- Health monitoring

### Event Coordination

Events enable:
- Asynchronous processing
- Cross-framework communication
- Audit trails
- Real-time monitoring

## Step-by-Step Tutorial

### Step 1: Set Up Your Environment

```bash
# Create a new project
mkdir my-orchestrator-project
cd my-orchestrator-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install business-logic-orchestrator redis
```

### Step 2: Configure Framework Connections

Create `config.yaml`:

```yaml
frameworks:
  langchain:
    api_key: ${LANGCHAIN_API_KEY}
    endpoint: https://api.langchain.com
    timeout: 30
    
  temporal:
    host: localhost
    port: 7233
    namespace: default
    
  mcp:
    server_url: http://localhost:8080
    auth_token: ${MCP_AUTH_TOKEN}
    
redis:
  host: localhost
  port: 6379
  db: 0
```

### Step 3: Create Your First Workflow

```python
from business_logic_orchestrator import MetaOrchestrator, BusinessRule
from business_logic_orchestrator.adapters import get_adapter

# Initialize
orchestrator = MetaOrchestrator.from_config("config.yaml")

# Define a simple rule programmatically
rule = BusinessRule(
    name="hello_world",
    conditions=lambda ctx: True,  # Always execute
    actions=[
        {
            "framework": "langchain",
            "action": "generate_text",
            "params": {"prompt": "Say hello!"}
        }
    ]
)

# Register and execute
orchestrator.register_rule(rule)
result = orchestrator.execute_rule("hello_world", {})

print(result)
```

### Step 4: Handle Complex Scenarios

```python
# Multi-framework coordination
async def process_document(document_path: str):
    """Process a document through multiple frameworks."""
    
    # Step 1: Extract text with MCP
    extraction_result = await orchestrator.execute_action(
        framework="mcp",
        action="extract_text",
        params={"path": document_path}
    )
    
    # Step 2: Analyze with LangChain
    analysis_result = await orchestrator.execute_action(
        framework="langchain",
        action="analyze_document",
        params={"text": extraction_result["text"]}
    )
    
    # Step 3: Create workflow with Temporal
    if analysis_result["requires_review"]:
        workflow_result = await orchestrator.execute_action(
            framework="temporal",
            action="start_review_workflow",
            params={
                "document_id": document_path,
                "analysis": analysis_result
            }
        )
    
    return {
        "extraction": extraction_result,
        "analysis": analysis_result,
        "workflow": workflow_result
    }
```

### Step 5: Monitor and Debug

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Set up monitoring
orchestrator.enable_monitoring(
    metrics_endpoint="http://localhost:9090",
    trace_endpoint="http://localhost:16686"
)

# Add custom event handlers
@orchestrator.on_event("rule_executed")
def log_rule_execution(event):
    print(f"Rule {event.rule_name} executed at {event.timestamp}")

@orchestrator.on_event("framework_error")
def handle_framework_error(event):
    print(f"Error in {event.framework}: {event.error}")
    # Implement recovery logic
```

## Best Practices

### 1. Rule Design
- Keep rules simple and focused
- Use descriptive names
- Document complex conditions
- Test rules in isolation

### 2. Error Handling
```python
try:
    result = orchestrator.execute_rule("risky_rule", context)
except FrameworkError as e:
    # Handle framework-specific errors
    logger.error(f"Framework error: {e}")
    result = orchestrator.execute_fallback("safe_rule", context)
except RuleEvaluationError as e:
    # Handle rule evaluation errors
    logger.error(f"Rule error: {e}")
```

### 3. Performance Optimization
```python
# Use parallel execution for independent actions
results = await orchestrator.execute_parallel([
    ("langchain", "task1", params1),
    ("mcp", "task2", params2),
    ("temporal", "task3", params3)
])

# Cache rule evaluation results
orchestrator.enable_caching(ttl=300)  # 5 minutes

# Batch event processing
orchestrator.configure_event_batching(
    batch_size=100,
    flush_interval=1.0  # seconds
)
```

## Common Patterns

### Pattern 1: Conditional Framework Selection
```python
rule = BusinessRule(
    name="dynamic_framework_selection",
    conditions=lambda ctx: ctx.get("data_size") > 1000000,
    actions=[
        {
            "framework": "temporal",  # Use Temporal for large data
            "action": "batch_process"
        }
    ],
    fallback_actions=[
        {
            "framework": "langchain",  # Use LangChain for small data
            "action": "quick_process"
        }
    ]
)
```

### Pattern 2: Event-Driven Coordination
```python
# Publish event from one framework
orchestrator.publish_event(
    "data_processed",
    {"file_id": "123", "status": "complete"}
)

# React in another framework
@orchestrator.on_event("data_processed")
async def trigger_next_step(event):
    if event.data["status"] == "complete":
        await orchestrator.execute_action(
            "langchain",
            "generate_report",
            {"file_id": event.data["file_id"]}
        )
```

## Next Steps

- Explore [advanced patterns](./advanced_patterns.md)
- Learn about [production deployment](./deployment.md)
- Read the [API reference](../api/reference.md)
- Join our [community](https://discord.gg/orchestrator)