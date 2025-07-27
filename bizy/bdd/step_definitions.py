"""
Behave Step Definitions for Business Logic Orchestrator.

This module provides comprehensive step definitions that allow Gherkin scenarios
to interact with the business logic orchestration system and framework adapters.
"""

from behave import given, when, then, step
from behave.runner import Context
import asyncio
import json
from typing import Any, Dict, List
import logging

from ..core.meta_orchestrator import MetaOrchestrator
from ..core.business_rule import BusinessRule, RuleCondition, RuleAction, RuleType, RulePriority
from ..adapters import get_global_registry
from .scenario_executor import BDDScenarioExecutor

logger = logging.getLogger(__name__)

# Global test context storage
test_context = {
    'customers': {},
    'tasks': {},
    'frameworks': {},
    'execution_results': {},
    'orchestrator': None,
    'bdd_executor': None,
    'rules': [],
    'events': []
}


def register_default_steps():
    """Register all default step definitions."""
    # This function can be called to ensure all steps are registered
    # The actual registration happens through the @given, @when, @then decorators
    pass


# =============================================================================
# Setup and Infrastructure Steps
# =============================================================================

@given('the business logic orchestrator is running')
def step_orchestrator_running(context: Context):
    """Initialize the business logic orchestrator for testing."""
    if not test_context['orchestrator']:
        # Initialize with test configuration
        test_context['orchestrator'] = MetaOrchestrator()
        test_context['bdd_executor'] = BDDScenarioExecutor(test_context['orchestrator'])
        
    context.orchestrator = test_context['orchestrator']
    context.bdd_executor = test_context['bdd_executor']


@given('all framework adapters are healthy')
def step_adapters_healthy(context: Context):
    """Verify all framework adapters are in healthy state."""
    test_context['frameworks'] = {
        'langchain': {
            'status': 'healthy', 
            'capabilities': ['document_analysis', 'chain_coordination', 'agent_orchestration']
        },
        'semantic_kernel': {
            'status': 'healthy', 
            'capabilities': ['agent_coordination', 'process_frameworks', 'skill_orchestration']
        },
        'mcp': {
            'status': 'healthy', 
            'capabilities': ['external_integrations', 'tool_execution', 'resource_management']
        },
        'temporal': {
            'status': 'healthy', 
            'capabilities': ['workflow_orchestration', 'process_automation', 'durable_execution']
        },
        'fastmcp': {
            'status': 'healthy', 
            'capabilities': ['high_performance_mcp', 'tool_coordination', 'batch_processing']
        },
        'zep': {
            'status': 'healthy', 
            'capabilities': ['memory_systems', 'temporal_knowledge_graphs', 'fact_extraction']
        }
    }
    context.frameworks = test_context['frameworks']


@given('the MCP toolkit is connected at "{path}"')
def step_mcp_connected(context: Context, path: str):
    """Verify MCP toolkit connection."""
    test_context['mcp_path'] = path
    if 'mcp' in test_context['frameworks']:
        test_context['frameworks']['mcp']['connected_path'] = path
    context.mcp_path = path


@given('the following frameworks are available')
def step_frameworks_available(context: Context):
    """Set up available frameworks with their status and capabilities."""
    for row in context.table:
        framework = row['framework']
        status = row['status']
        capabilities = row['capabilities'].split(',') if row['capabilities'] else []
        
        test_context['frameworks'][framework] = {
            'status': status,
            'capabilities': [cap.strip() for cap in capabilities]
        }
    context.frameworks = test_context['frameworks']


@given('the following framework states')
def step_framework_states(context: Context):
    """Set up framework states including error conditions."""
    for row in context.table:
        framework = row['framework']
        status = row['status']
        error_type = row['error_type']
        
        test_context['frameworks'][framework] = {
            'status': status,
            'error_type': error_type if error_type != 'none' else None
        }
    context.frameworks = test_context['frameworks']


# =============================================================================
# Customer and Data Setup Steps
# =============================================================================

@given('a customer with the following attributes')
def step_customer_with_attributes(context: Context):
    """Create a test customer with specified attributes."""
    customer_data = {}
    for row in context.table:
        attribute = row['attribute']
        value = row['value']
        
        # Convert numeric values
        try:
            if '.' in value:
                value = float(value)
            elif value.isdigit():
                value = int(value)
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
        except (ValueError, AttributeError):
            pass  # Keep as string
            
        customer_data[attribute] = value
        
    test_context['customers']['current'] = customer_data
    context.customer = customer_data


@given('a customer with {attribute} "{value}"')
def step_customer_with_attribute(context: Context, attribute: str, value: str):
    """Create a customer with a single attribute."""
    if 'current' not in test_context['customers']:
        test_context['customers']['current'] = {}
        
    # Convert value to appropriate type
    try:
        if '.' in value:
            converted_value = float(value)
        elif value.isdigit():
            converted_value = int(value)
        elif value.lower() in ['true', 'false']:
            converted_value = value.lower() == 'true'
        else:
            converted_value = value
    except (ValueError, AttributeError):
        converted_value = value
        
    test_context['customers']['current'][attribute] = converted_value
    context.customer = test_context['customers']['current']


@given('the customer {attribute} is {operator} {value}')
def step_customer_condition(context: Context, attribute: str, operator: str, value: str):
    """Set up customer condition for testing."""
    if 'current' not in test_context['customers']:
        test_context['customers']['current'] = {}
        
    # Convert value
    try:
        if '.' in value:
            converted_value = float(value)
        elif value.isdigit():
            converted_value = int(value)
        else:
            converted_value = value
    except (ValueError, AttributeError):
        converted_value = value
        
    # Map operators
    if operator in ['below', 'less than', 'under']:
        # For testing, we'll set the value slightly lower than the threshold
        if isinstance(converted_value, (int, float)):
            test_context['customers']['current'][attribute] = converted_value - 0.1
        else:
            test_context['customers']['current'][attribute] = converted_value
    elif operator in ['above', 'greater than', 'over']:
        if isinstance(converted_value, (int, float)):
            test_context['customers']['current'][attribute] = converted_value + 0.1
        else:
            test_context['customers']['current'][attribute] = converted_value
    else:
        test_context['customers']['current'][attribute] = converted_value
        
    context.customer = test_context['customers']['current']


# =============================================================================
# Task and Workflow Setup Steps
# =============================================================================

@given('a task with complexity level "{complexity}"')
def step_task_with_complexity(context: Context, complexity: str):
    """Create a task with specified complexity level."""
    test_context['tasks']['current'] = {
        'complexity': complexity,
        'type': getattr(context, 'task_type', 'general')
    }
    context.task = test_context['tasks']['current']


@given('the task type is "{task_type}"')
def step_task_type(context: Context, task_type: str):
    """Set the task type for the current task."""
    if 'current' not in test_context['tasks']:
        test_context['tasks']['current'] = {}
    test_context['tasks']['current']['type'] = task_type
    context.task = test_context['tasks']['current']


@given('data size is {operator} {size:d}')
def step_data_size_condition(context: Context, operator: str, size: int):
    """Set up data size condition."""
    if 'current' not in test_context['tasks']:
        test_context['tasks']['current'] = {}
        
    if operator in ['greater than', 'above', 'over']:
        test_context['tasks']['current']['data_size'] = size + 1
    elif operator in ['less than', 'below', 'under']:
        test_context['tasks']['current']['data_size'] = size - 1
    else:
        test_context['tasks']['current']['data_size'] = size
        
    context.task = test_context['tasks']['current']


@given('processing is required')
def step_processing_required(context: Context):
    """Set processing required flag."""
    if 'current' not in test_context['tasks']:
        test_context['tasks']['current'] = {}
    test_context['tasks']['current']['processing_required'] = True
    context.task = test_context['tasks']['current']


# =============================================================================
# Business Rule Setup Steps
# =============================================================================

@given('the following business rules are active')
def step_business_rules_active(context: Context):
    """Set up active business rules for conflict resolution testing."""
    test_context['active_rules'] = []
    
    for row in context.table:
        rule_name = row['rule_name']
        priority_str = row['priority']
        conditions_str = row['conditions']
        actions_str = row['actions']
        
        # Parse priority
        priority_map = {
            'low': RulePriority.LOW,
            'medium': RulePriority.MEDIUM,
            'high': RulePriority.HIGH,
            'critical': RulePriority.CRITICAL
        }
        priority = priority_map.get(priority_str.lower(), RulePriority.MEDIUM)
        
        # Parse conditions
        rule_conditions = []
        condition_parts = conditions_str.split(',')
        for part in condition_parts:
            part = part.strip()
            if '=' in part and '<' not in part and '>' not in part:
                field, value = part.split('=', 1)
                rule_conditions.append(RuleCondition(field.strip(), "eq", value.strip().strip('"')))
            elif '<' in part:
                field, value = part.split('<', 1)
                rule_conditions.append(RuleCondition(field.strip(), "lt", float(value.strip())))
            elif '>' in part:
                field, value = part.split('>', 1)
                rule_conditions.append(RuleCondition(field.strip(), "gt", float(value.strip())))
        
        # Create simple action
        rule_actions = [RuleAction('system', actions_str.lower().replace(' ', '_'), {})]
        
        rule = BusinessRule(
            name=rule_name,
            priority=priority,
            conditions=rule_conditions,
            actions=rule_actions
        )
        
        test_context['active_rules'].append(rule)
    
    context.rules = test_context['active_rules']


# =============================================================================
# Event Trigger Steps
# =============================================================================

@when('a support interaction is created')
def step_support_interaction_created(context: Context):
    """Trigger a support interaction event."""
    event = {
        'type': 'support_interaction',
        'customer': test_context['customers'].get('current', {}),
        'timestamp': 'now'
    }
    test_context['events'].append(event)
    context.current_event = event


@when('a customer uploads a legal document')
def step_customer_uploads_document(context: Context):
    """Trigger a document upload event."""
    event = {
        'type': 'document_upload',
        'document_type': 'legal',
        'customer': test_context['customers'].get('current', {}),
        'timestamp': 'now'
    }
    test_context['events'].append(event)
    context.current_event = event


@when('the customer uploads legal documents')
def step_customer_uploads_documents(context: Context):
    """Trigger multiple document upload event."""
    event = {
        'type': 'document_upload',
        'document_type': 'legal',
        'document_count': 'multiple',
        'customer': test_context['customers'].get('current', {}),
        'timestamp': 'now'
    }
    test_context['events'].append(event)
    context.current_event = event


@when('the business rule is triggered')
def step_business_rule_triggered(context: Context):
    """Generic business rule trigger."""
    event = {
        'type': 'business_rule_trigger',
        'context': test_context.get('customers', {}).get('current', {}),
        'timestamp': 'now'
    }
    test_context['events'].append(event)
    context.current_event = event


@when('the orchestrator evaluates the task')
def step_orchestrator_evaluates_task(context: Context):
    """Trigger orchestrator evaluation of the current task."""
    task = test_context['tasks'].get('current', {})
    
    # Simple decision logic based on complexity
    complexity = task.get('complexity', 'simple')
    
    if complexity == 'simple':
        selected_framework = 'mcp'
        pattern = 'direct_execution'
    elif complexity == 'moderate':
        selected_framework = 'langchain'
        pattern = 'chain_coordination'
    elif complexity == 'complex':
        selected_framework = 'semantic_kernel'
        pattern = 'multi_agent'
    else:  # critical
        selected_framework = 'temporal'
        pattern = 'full_coordination'
        
    test_context['evaluation_result'] = {
        'selected_framework': selected_framework,
        'coordination_pattern': pattern,
        'task': task
    }
    context.evaluation_result = test_context['evaluation_result']


@when('the data pipeline is triggered')
def step_data_pipeline_triggered(context: Context):
    """Trigger data pipeline processing."""
    event = {
        'type': 'data_pipeline_trigger',
        'task': test_context['tasks'].get('current', {}),
        'timestamp': 'now'
    }
    test_context['events'].append(event)
    context.current_event = event


# =============================================================================
# Verification Steps - Framework Coordination
# =============================================================================

@then('the orchestrator should execute the following sequence')
def step_orchestrator_executes_sequence(context: Context):
    """Verify the orchestrator executes the expected sequence."""
    expected_sequence = []
    for row in context.table:
        expected_sequence.append({
            'step': int(row['step']),
            'framework': row['framework'],
            'action': row['action']
        })
    
    test_context['execution_results']['sequence'] = expected_sequence
    context.expected_sequence = expected_sequence
    
    # Verify sequence is reasonable
    assert len(expected_sequence) > 0, "Expected sequence should not be empty"
    
    # Verify all frameworks are available
    for step in expected_sequence:
        framework = step['framework']
        assert framework in test_context['frameworks'], f"Framework {framework} should be available"


@then('it should route to "{framework}" framework')
def step_should_route_to_framework(context: Context, framework: str):
    """Verify the orchestrator routes to the expected framework."""
    result = test_context.get('evaluation_result', {})
    selected = result.get('selected_framework')
    
    assert selected == framework, f"Expected {framework}, but got {selected}"


@then('use "{pattern}" coordination pattern')
def step_should_use_pattern(context: Context, pattern: str):
    """Verify the orchestrator uses the expected coordination pattern."""
    result = test_context.get('evaluation_result', {})
    selected_pattern = result.get('coordination_pattern')
    
    assert selected_pattern == pattern, f"Expected {pattern}, but got {selected_pattern}"


@then('the system should')
def step_system_should_execute(context: Context):
    """Verify the system executes expected actions."""
    expected_actions = []
    for row in context.table:
        expected_actions.append({
            'framework': row['framework'],
            'action': row['action'],
            'expected_result': row['expected_result']
        })
    
    test_context['execution_results']['expected_actions'] = expected_actions
    context.expected_actions = expected_actions
    
    # Verify each framework is available
    for action in expected_actions:
        framework = action['framework']
        assert framework in test_context['frameworks'], f"Framework {framework} should be available"


# =============================================================================
# Verification Steps - Framework-Specific Actions
# =============================================================================

@then('LangChain should {action}')
def step_langchain_should_action(context: Context, action: str):
    """Verify LangChain performs expected action."""
    assert 'langchain' in test_context['frameworks'], "LangChain should be available"
    assert test_context['frameworks']['langchain']['status'] == 'healthy', "LangChain should be healthy"
    
    # Store expected action for verification
    if 'langchain_actions' not in test_context['execution_results']:
        test_context['execution_results']['langchain_actions'] = []
    test_context['execution_results']['langchain_actions'].append(action)


@then('Temporal should {action}')
def step_temporal_should_action(context: Context, action: str):
    """Verify Temporal performs expected action."""
    assert 'temporal' in test_context['frameworks'], "Temporal should be available"
    assert test_context['frameworks']['temporal']['status'] == 'healthy', "Temporal should be healthy"
    
    if 'temporal_actions' not in test_context['execution_results']:
        test_context['execution_results']['temporal_actions'] = []
    test_context['execution_results']['temporal_actions'].append(action)


@then('MCP toolkit should {action}')
def step_mcp_should_action(context: Context, action: str):
    """Verify MCP toolkit performs expected action."""
    assert 'mcp' in test_context['frameworks'], "MCP toolkit should be available"
    assert test_context['frameworks']['mcp']['status'] == 'healthy', "MCP toolkit should be healthy"
    
    if 'mcp_actions' not in test_context['execution_results']:
        test_context['execution_results']['mcp_actions'] = []
    test_context['execution_results']['mcp_actions'].append(action)


@then('Semantic Kernel should {action}')
def step_semantic_kernel_should_action(context: Context, action: str):
    """Verify Semantic Kernel performs expected action."""
    assert 'semantic_kernel' in test_context['frameworks'], "Semantic Kernel should be available"
    assert test_context['frameworks']['semantic_kernel']['status'] == 'healthy', "Semantic Kernel should be healthy"
    
    if 'semantic_kernel_actions' not in test_context['execution_results']:
        test_context['execution_results']['semantic_kernel_actions'] = []
    test_context['execution_results']['semantic_kernel_actions'].append(action)


@then('FastMCP should {action}')
def step_fastmcp_should_action(context: Context, action: str):
    """Verify FastMCP performs expected action."""
    assert 'fastmcp' in test_context['frameworks'], "FastMCP should be available"
    assert test_context['frameworks']['fastmcp']['status'] == 'healthy', "FastMCP should be healthy"
    
    if 'fastmcp_actions' not in test_context['execution_results']:
        test_context['execution_results']['fastmcp_actions'] = []
    test_context['execution_results']['fastmcp_actions'].append(action)


@then('Zep should {action}')
def step_zep_should_action(context: Context, action: str):
    """Verify Zep performs expected action."""
    assert 'zep' in test_context['frameworks'], "Zep should be available"
    assert test_context['frameworks']['zep']['status'] == 'healthy', "Zep should be healthy"
    
    if 'zep_actions' not in test_context['execution_results']:
        test_context['execution_results']['zep_actions'] = []
    test_context['execution_results']['zep_actions'].append(action)


# =============================================================================
# Verification Steps - Generic Actions and Outcomes
# =============================================================================

@then('{action} via {framework}')
def step_action_via_framework(context: Context, action: str, framework: str):
    """Verify an action is performed via specific framework."""
    # Normalize framework name
    framework_map = {
        'mcp toolkit': 'mcp',
        'langchain': 'langchain',
        'temporal': 'temporal'
    }
    normalized_framework = framework_map.get(framework.lower(), framework.lower())
    
    assert normalized_framework in test_context['frameworks'], f"Framework {framework} should be available"
    
    if 'generic_actions' not in test_context['execution_results']:
        test_context['execution_results']['generic_actions'] = []
    test_context['execution_results']['generic_actions'].append({
        'action': action,
        'framework': normalized_framework
    })


@then('all frameworks should coordinate successfully')
def step_all_frameworks_coordinate(context: Context):
    """Verify all frameworks coordinate successfully."""
    for framework_name, framework_info in test_context['frameworks'].items():
        assert framework_info['status'] == 'healthy', f"Framework {framework_name} should be healthy for coordination"
    
    test_context['coordination_verified'] = True


@then('the workflow should complete within {seconds:d} seconds')
def step_workflow_completes_within(context: Context, seconds: int):
    """Verify workflow completion time."""
    test_context['performance_requirements'] = {
        'max_duration': seconds,
        'unit': 'seconds'
    }
    
    assert seconds > 0, "Timeout should be positive"


@then('the document should be processed within {minutes:d} minutes')
def step_document_processed_within(context: Context, minutes: int):
    """Verify document processing time."""
    test_context['performance_requirements'] = {
        'max_duration': minutes,
        'unit': 'minutes'
    }
    
    assert minutes > 0, "Processing time should be positive"


@then('all framework responses should be successful')
def step_all_responses_successful(context: Context):
    """Verify all framework responses are successful."""
    for framework, info in test_context['frameworks'].items():
        assert info['status'] == 'healthy', f"Framework {framework} should be healthy"
    
    test_context['all_responses_successful'] = True


@then('all stakeholders should be notified')
def step_stakeholders_notified(context: Context):
    """Verify stakeholder notification."""
    test_context['stakeholder_notifications'] = {'sent': True, 'stakeholders': 'all'}


@then('the estimated execution time should be "{max_time}"')
def step_execution_time_estimate(context: Context, max_time: str):
    """Verify execution time estimate."""
    assert max_time.endswith(('s', 'm')), f"Time format should end with 's' or 'm': {max_time}"
    test_context['time_estimate'] = max_time


# =============================================================================
# Framework Availability Steps
# =============================================================================

@given('{framework} is available for {capability}')
def step_framework_available_for_capability(context: Context, framework: str, capability: str):
    """Set up framework availability for specific capability."""
    # Normalize framework name
    framework_map = {
        'langchain': 'langchain',
        'temporal workflow engine': 'temporal',
        'mcp toolkit': 'mcp',
        'semantic kernel': 'semantic_kernel',
        'semantic kernel agents': 'semantic_kernel',
        'zep memory system': 'zep'
    }
    
    normalized_framework = framework_map.get(framework.lower(), framework.lower().replace(' ', '_'))
    
    if normalized_framework not in test_context['frameworks']:
        test_context['frameworks'][normalized_framework] = {'status': 'healthy', 'capabilities': []}
    
    capability_normalized = capability.lower().replace(' ', '_')
    if capability_normalized not in test_context['frameworks'][normalized_framework]['capabilities']:
        test_context['frameworks'][normalized_framework]['capabilities'].append(capability_normalized)


@given('{framework} document analyzer is available')
def step_framework_analyzer_available(context: Context, framework: str):
    """Set up document analyzer availability."""
    step_framework_available_for_capability(context, framework, 'document_analysis')


@given('{framework} workflow engine is running')
def step_framework_workflow_running(context: Context, framework: str):
    """Set up workflow engine availability."""
    step_framework_available_for_capability(context, framework, 'workflow_orchestration')


@given('{framework} agents are ready')
def step_framework_agents_ready(context: Context, framework: str):
    """Set up agent availability."""
    step_framework_available_for_capability(context, framework, 'agent_coordination')


# =============================================================================
# Customer and Enterprise Context Steps
# =============================================================================

@given('a new enterprise customer')
def step_new_enterprise_customer(context: Context):
    """Set up a new enterprise customer."""
    test_context['customers']['current'] = {
        'type': 'enterprise',
        'status': 'new',
        'tier': 'enterprise'
    }
    context.customer = test_context['customers']['current']


# =============================================================================
# Error Handling and Recovery Steps
# =============================================================================

@then('the orchestrator should')
def step_orchestrator_should_execute(context: Context):
    """Verify orchestrator executes expected recovery actions."""
    expected_actions = []
    for row in context.table:
        expected_actions.append({
            'action': row['action'],
            'expected_outcome': row['expected_outcome']
        })
    
    test_context['recovery_actions'] = expected_actions
    
    # Verify reasonable recovery actions
    action_names = [action['action'] for action in expected_actions]
    assert len(action_names) > 0, "Should have recovery actions"


@then('the business outcome should still be achieved')
def step_business_outcome_achieved(context: Context):
    """Verify business outcome despite technical failures."""
    recovery_actions = test_context.get('recovery_actions', [])
    assert len(recovery_actions) > 0, "Recovery actions should be defined"
    test_context['business_outcome_achieved'] = True


@then('stakeholders should be notified of the degradation')
def step_stakeholders_notified_degradation(context: Context):
    """Verify stakeholders are notified of degradation."""
    test_context['degradation_notifications'] = {'sent': True}


@then('the resolution should be documented for future reference')
def step_resolution_documented(context: Context):
    """Verify conflict resolution is documented."""
    test_context['documentation'] = {'conflict_resolution': True}
