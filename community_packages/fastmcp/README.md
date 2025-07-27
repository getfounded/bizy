# Bizy FastMCP Extensions

Enterprise-grade extensions that bring Bizy's business context awareness and rule evaluation to FastMCP tools.

## Overview

This package extends FastMCP with powerful business logic capabilities:

- **Business Context Extension**: Add business context metadata to tool execution
- **Tool Transformers**: Transform tool behavior based on business rules
- **Framework Bridge**: Connect FastMCP tools with other AI frameworks
- **Security & Compliance**: Enforce access controls and audit logging

## Features

### 🔒 Business Context Awareness
Add business context to every tool execution:

```python
from bizy_fastmcp import BusinessContextExtension, BusinessContext

# Create business context
context = BusinessContext(
    user_role="analyst",
    department="Finance",
    clearance_level=2,
    active_rules=["data_privacy", "cost_control"]
)

# Tools automatically respect business context
result = await server.call_tool("query_data", args, context)
```

### 🔄 Tool Transformation
Transform tools with business rule evaluation:

```python
from bizy_fastmcp.transformers import BusinessRuleTransformer

transformer = BusinessRuleTransformer(orchestrator)
enhanced_tool = transformer.transform_tool(original_tool)
```

### 🌉 Cross-Framework Integration
Bridge FastMCP tools with other frameworks:

```python
from bizy_fastmcp.extensions import FrameworkBridgeExtension

bridge = FrameworkBridgeExtension()
bridge.connect_framework("langchain", langchain_adapter)
bridge.enable_tool_sharing("fastmcp_tool", ["langchain", "temporal"])
```

## Installation

```bash
pip install bizy-fastmcp
```

## Quick Start

### 1. Basic Business Context Setup

```python
from fastmcp import FastMCP
from bizy_fastmcp import BusinessContextExtension

# Initialize server and extension
server = FastMCP("Business-Aware Server")
extension = BusinessContextExtension()

# Register business rules
extension.register_rule(
    "sensitive_data_tool",
    create_department_rule("HR", ["query_employee_data"])
)

# Apply to server
extension.apply_to_server(server)
```

### 2. Tool Enhancement with Rules

```python
# Define a business-aware tool
@server.tool()
@business_context_required(required_clearance=2)
async def process_payment(amount: float, recipient: str) -> dict:
    """Process payment with clearance checks."""
    return {"status": "processed", "amount": amount}
```

### 3. Audit and Compliance

```python
# Set up audit logging
extension.set_audit_logger(audit_handler)

# All tool executions are automatically logged
# with business context and rule evaluations
```

## Use Cases

### Access Control
Control tool access based on user roles and departments:

```python
# Only HR can access employee data
rule = create_department_rule("HR", ["employee_tools"])
extension.register_rule("query_employees", rule)
```

### Data Governance
Enforce data limits and privacy rules:

```python
# Limit data exports to 1000 records
rule = create_data_limit_rule(max_records=1000)
extension.register_rule("export_data", rule)
```

### Transaction Controls
Require approval for high-value operations:

```python
# Require level 3 clearance for transactions over $10,000
rule = create_clearance_rule(
    min_clearance=3,
    condition=lambda ctx, args: args.get("amount", 0) > 10000
)
```

## Architecture

The extensions follow FastMCP's design principles while adding:

1. **Context Propagation**: Business context flows through all tool calls
2. **Rule Engine**: Evaluate business rules before and after execution
3. **Transformation Pipeline**: Modify tool behavior without changing code
4. **Audit Trail**: Complete audit logging for compliance

## Examples

See the `examples/` directory for complete working examples:

- `business_context_demo.py`: Context-aware tool execution
- `rule_enforcement_demo.py`: Business rule patterns  
- `cross_framework_demo.py`: Multi-framework integration

## Performance Optimization

The extensions are designed for minimal overhead:

- Rule evaluation: < 1ms for most rules
- Context extraction: Zero-copy where possible
- Async throughout for non-blocking execution

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [https://docs.bizy.work](https://docs.bizy.work)
- Issues: [GitHub Issues](https://github.com/getfounded/bizy/issues)
- Discussions: [GitHub Discussions](https://github.com/getfounded/bizy/discussions)