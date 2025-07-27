"""Example: Business Context Integration with FastMCP.

This example demonstrates how to enhance FastMCP tools with business
context awareness and rule evaluation.
"""

from fastmcp import FastMCP, Context
import sys
sys.path.append("../../..")

from business_logic_orchestrator.core.meta_orchestrator import MetaOrchestrator
from community_packages.fastmcp.extensions import BusinessContextExtension
from community_packages.fastmcp.extensions.business_context_extension import (
    BusinessContext,
    BusinessRule,
    create_department_rule,
    create_data_limit_rule
)
from community_packages.fastmcp.transformers import BusinessRuleTransformer

async def setup_business_aware_server():
    """Set up a FastMCP server with business logic integration."""
    
    # Initialize FastMCP server
    server = FastMCP("Business-Aware MCP Server")
    
    # Initialize Business Logic Orchestrator
    orchestrator = MetaOrchestrator()
    
    # Create and apply business context extension
    context_extension = BusinessContextExtension(orchestrator)
    
    # Register business rules
    # Rule 1: Restrict sensitive data tool to HR department
    context_extension.register_rule(
        "query_employee_data",
        create_department_rule("HR", ["query_employee_data"])
    )
    
    # Rule 2: Limit data queries to 1000 records
    context_extension.register_rule(
        "query_database",
        create_data_limit_rule(1000)
    )
    
    # Rule 3: Custom rule for financial transactions
    def financial_rule_condition(context: BusinessContext, args: Dict[str, Any]) -> bool:
        amount = args.get("amount", 0)
        return amount > 10000 and context.clearance_level < 3
    
    financial_rule = BusinessRule(
        name="high_value_transaction",
        description="Require level 3 clearance for transactions over $10,000",
        condition=financial_rule_condition,
        action="deny",
        priority=20
    )
    
    context_extension.register_rule("process_transaction", financial_rule)
    
    # Apply extension to server
    context_extension.apply_to_server(server)
    
    # Define business-aware tools
    @server.tool()
    async def query_employee_data(
        employee_id: str,
        fields: List[str],
        context: Context
    ) -> Dict[str, Any]:
        """Query employee data with department restrictions."""
        # This will only execute if business rules allow
        return {
            "employee_id": employee_id,
            "data": {field: f"[{field} data]" for field in fields},
            "accessed_by": context.get("department", "unknown")
        }
    
    @server.tool()
    async def query_database(
        table: str,
        limit: int = 100,
        context: Context
    ) -> List[Dict[str, Any]]:
        """Query database with automatic limit enforcement."""
        # Limit will be enforced by business rules
        return [
            {"id": i, "table": table, "data": f"Record {i}"}
            for i in range(min(limit, 1000))  # Double safety
        ]
    
    @server.tool()
    async def process_transaction(
        amount: float,
        recipient: str,
        context: Context
    ) -> Dict[str, Any]:
        """Process financial transaction with clearance checks."""
        return {
            "transaction_id": "TXN123456",
            "amount": amount,
            "recipient": recipient,
            "status": "processed",
            "approved_by": context.get("user_role", "unknown")
        }
    
    return server, context_extension

async def demonstrate_rule_enforcement():
    """Demonstrate business rule enforcement in action."""
    
    # Set up server
    server, extension = await setup_business_aware_server()
    
    print("=== Business Context Demo ===\n")
    
    # Test Case 1: HR accessing employee data (allowed)
    print("Test 1: HR department accessing employee data")
    hr_context = Context({
        "department": "HR",
        "user_role": "hr_manager",
        "clearance_level": 2
    })
    
    try:
        result = await server.call_tool(
            "query_employee_data",
            {"employee_id": "EMP001", "fields": ["name", "salary"]},
            hr_context
        )
        print(f"✓ Success: {result}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Test Case 2: Non-HR accessing employee data (denied)
    print("Test 2: Finance department accessing employee data")
    finance_context = Context({
        "department": "Finance",
        "user_role": "analyst",
        "clearance_level": 1
    })
    
    try:
        result = await server.call_tool(
            "query_employee_data",
            {"employee_id": "EMP001", "fields": ["name", "salary"]},
            finance_context
        )
        print(f"✓ Success: {result}\n")
    except Exception as e:
        print(f"✗ Expected denial: {e}\n")
    
    # Test Case 3: Data limit enforcement
    print("Test 3: Querying with excessive limit")
    general_context = Context({
        "department": "Analytics",
        "user_role": "analyst",
        "clearance_level": 1
    })
    
    try:
        result = await server.call_tool(
            "query_database",
            {"table": "customers", "limit": 5000},
            general_context
        )
        print(f"✓ Limited to: {len(result)} records\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Test Case 4: High-value transaction with insufficient clearance
    print("Test 4: High-value transaction with low clearance")
    try:
        result = await server.call_tool(
            "process_transaction",
            {"amount": 15000, "recipient": "ACCT789"},
            general_context
        )
        print(f"✓ Success: {result}\n")
    except Exception as e:
        print(f"✗ Expected denial: {e}\n")
    
    # Test Case 5: High-value transaction with sufficient clearance
    print("Test 5: High-value transaction with proper clearance")
    executive_context = Context({
        "department": "Executive",
        "user_role": "cfo",
        "clearance_level": 4
    })
    
    try:
        result = await server.call_tool(
            "process_transaction",
            {"amount": 15000, "recipient": "ACCT789"},
            executive_context
        )
        print(f"✓ Success: {result}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")

async def demonstrate_tool_transformation():
    """Demonstrate tool transformation with business rules."""
    
    # Initialize components
    orchestrator = MetaOrchestrator()
    transformer = BusinessRuleTransformer(orchestrator)
    
    # Map tools to rule sets
    transformer.map_tool_to_rule_set("data_export", "export_rules")
    transformer.map_tool_to_rule_set("api_call", "external_api_rules")
    
    # Create FastMCP server
    server = FastMCP("Transformed Tool Server")
    
    # Define original tool
    @server.tool()
    async def data_export(
        format: str,
        include_pii: bool = False
    ) -> Dict[str, Any]:
        """Export data in specified format."""
        return {
            "format": format,
            "include_pii": include_pii,
            "records_exported": 1000
        }
    
    # Transform the tool
    original_tool = server.get_tool("data_export")
    transformed_tool = transformer.transform_tool(original_tool)
    
    # Replace with transformed version
    server.tools["data_export"] = transformed_tool
    
    print("\n=== Tool Transformation Demo ===\n")
    
    # Test transformed tool
    context = Context({
        "user_role": "analyst",
        "department": "Analytics"
    })
    
    try:
        result = await server.call_tool(
            "data_export",
            {"format": "csv", "include_pii": True},
            context
        )
        print(f"Export result: {result}")
    except Exception as e:
        print(f"Business rule evaluation: {e}")

if __name__ == "__main__":
    import asyncio
    
    # Run demonstrations
    asyncio.run(demonstrate_rule_enforcement())
    asyncio.run(demonstrate_tool_transformation())