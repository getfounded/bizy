"""Example: Business Logic Integration with LangChain.

This example demonstrates how to use the Business Logic Orchestrator
with LangChain for complex decision-making workflows.
"""

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Import Bizy components
import sys
sys.path.append("../../..")
from bizy.core.meta_orchestrator import MetaOrchestrator
from bizy.adapters.langchain_adapter import LangChainAdapter
from community_packages.langchain.business_logic_chains import (
    BusinessRuleChain,
    CrossFrameworkChain,
    RuleEvaluationChain
)

def create_customer_service_workflow():
    """Create a customer service workflow with business logic."""
    
    # Initialize orchestrator
    orchestrator = MetaOrchestrator()
    
    # Register LangChain adapter
    langchain_adapter = LangChainAdapter()
    orchestrator.register_adapter("langchain", langchain_adapter)
    
    # Create business rule chain for customer escalation
    escalation_chain = BusinessRuleChain.from_orchestrator(
        orchestrator=orchestrator,
        rule_name="customer_escalation",
        verbose=True
    )
    
    # Create LLM chain for response generation
    llm = OpenAI(temperature=0.7)
    response_template = """
    Based on the business rule evaluation:
    Decision: {decision}
    Reason: {reason}
    
    Generate an appropriate customer service response:
    """
    
    response_prompt = PromptTemplate(
        input_variables=["decision", "reason"],
        template=response_template
    )
    
    response_chain = LLMChain(
        llm=llm,
        prompt=response_prompt,
        verbose=True
    )
    
    # Combine chains
    from langchain.chains import SequentialChain
    
    workflow = SequentialChain(
        chains=[escalation_chain, response_chain],
        input_variables=["input"],
        output_variables=["output"],
        verbose=True
    )
    
    return workflow

def create_cross_framework_workflow():
    """Create a workflow that coordinates multiple frameworks."""
    
    # Initialize orchestrator
    orchestrator = MetaOrchestrator()
    
    # Configure cross-framework coordination
    config = {
        "frameworks": ["langchain", "temporal", "mcp_toolkit"],
        "action_sequence": [
            {
                "framework": "langchain",
                "action": "analyze_sentiment",
                "params": {"model": "sentiment-analysis"}
            },
            {
                "framework": "temporal",
                "action": "start_workflow",
                "params": {"workflow": "customer_response"},
                "update_context": True
            },
            {
                "framework": "mcp_toolkit",
                "action": "send_notification",
                "params": {"channel": "support_team"}
            }
        ]
    }
    
    # Create cross-framework chain
    cross_chain = CrossFrameworkChain.from_config(
        orchestrator=orchestrator,
        config=config,
        verbose=True
    )
    
    return cross_chain

def demonstrate_rule_evaluation():
    """Demonstrate complex rule evaluation with LLM reasoning."""
    
    # Initialize components
    orchestrator = MetaOrchestrator()
    llm = OpenAI(temperature=0.3)
    
    # Create prompt for rule reasoning
    rule_prompt = PromptTemplate(
        input_variables=["rule", "context", "basic_evaluation"],
        template="""
        Rule: {rule[name]}
        Context: {context}
        Basic Evaluation: {basic_evaluation}
        
        Provide detailed reasoning for this business rule evaluation,
        considering all relevant factors and edge cases.
        Include your confidence level (high/medium/low).
        """
    )
    
    # Create rule evaluation chain
    eval_chain = RuleEvaluationChain(
        llm=llm,
        prompt=rule_prompt,
        orchestrator=orchestrator,
        rule_set="fraud_detection",
        use_llm_reasoning=True,
        verbose=True
    )
    
    # Example evaluation
    result = eval_chain.run({
        "transaction_amount": 5000,
        "customer_history": "new",
        "location": "foreign",
        "time": "3am"
    })
    
    print("Evaluation Result:", result)

if __name__ == "__main__":
    print("=== Business Logic + LangChain Demo ===\n")
    
    print("1. Customer Service Workflow")
    workflow = create_customer_service_workflow()
    
    # Example customer interaction
    customer_input = {
        "sentiment_score": 0.2,
        "customer_tier": "premium",
        "issue_type": "billing",
        "interaction_count": 3
    }
    
    result = workflow.run(customer_input)
    print("Workflow Result:", result)
    
    print("\n2. Cross-Framework Coordination")
    cross_workflow = create_cross_framework_workflow()
    
    # Example cross-framework execution
    cross_input = {
        "customer_message": "I'm very frustrated with the service",
        "customer_id": "12345",
        "priority": "high"
    }
    
    cross_result = cross_workflow.run(cross_input)
    print("Cross-Framework Result:", cross_result)
    
    print("\n3. Complex Rule Evaluation")
    demonstrate_rule_evaluation()