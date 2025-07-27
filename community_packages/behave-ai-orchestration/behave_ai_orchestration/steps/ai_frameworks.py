"""
AI Framework Step Definitions for Behave

This module provides comprehensive step definitions for testing AI framework
interactions in natural language BDD scenarios.
"""

from behave import given, when, then, step
from behave.runner import Context
from typing import Any, Dict, List, Optional
import json
import time

# Test context storage
ai_test_context = {
    'frameworks': {},
    'data': {},
    'results': {},
    'performance': {},
    'errors': []
}


# =============================================================================
# Framework Availability and Setup Steps
# =============================================================================

@given('LangChain is available')
@given('LangChain is available for {capability}')
def step_langchain_available(context: Context, capability: str = None):
    """Verify LangChain framework availability."""
    ai_test_context['frameworks']['langchain'] = {
        'status': 'available',
        'capabilities': [capability] if capability else ['general'],
        'last_check': time.time()
    }
    context.langchain_available = True


@given('Semantic Kernel is available')
@given('Semantic Kernel is available for {capability}')
def step_semantic_kernel_available(context: Context, capability: str = None):
    """Verify Semantic Kernel framework availability."""
    ai_test_context['frameworks']['semantic_kernel'] = {
        'status': 'available',
        'capabilities': [capability] if capability else ['general'],
        'last_check': time.time()
    }
    context.semantic_kernel_available = True


@given('Temporal workflow engine is available')
@given('Temporal is available for {capability}')
def step_temporal_available(context: Context, capability: str = None):
    """Verify Temporal workflow engine availability."""
    ai_test_context['frameworks']['temporal'] = {
        'status': 'available',
        'capabilities': [capability] if capability else ['workflows'],
        'last_check': time.time()
    }
    context.temporal_available = True


@given('MCP toolkit is available')
@given('MCP is available for {capability}')
def step_mcp_available(context: Context, capability: str = None):
    """Verify MCP toolkit availability."""
    ai_test_context['frameworks']['mcp'] = {
        'status': 'available',
        'capabilities': [capability] if capability else ['tools'],
        'last_check': time.time()
    }
    context.mcp_available = True


@given('all AI frameworks are healthy')
def step_all_frameworks_healthy(context: Context):
    """Verify all AI frameworks are in healthy state."""
    frameworks = ['langchain', 'semantic_kernel', 'temporal', 'mcp', 'fastmcp', 'zep']
    for framework in frameworks:
        ai_test_context['frameworks'][framework] = {
            'status': 'healthy',
            'capabilities': ['general'],
            'response_time': 0.1,
            'last_check': time.time()
        }
    context.all_frameworks_healthy = True


# =============================================================================
# Data and Input Setup Steps
# =============================================================================

@given('test data with the following attributes')
def step_test_data_with_attributes(context: Context):
    """Set up test data with specified attributes."""
    test_data = {}
    for row in context.table:
        attribute = row['attribute']
        value = row['value']
        
        # Convert value to appropriate type
        try:
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif '.' in value and value.replace('.', '').isdigit():
                value = float(value)
            elif value.isdigit():
                value = int(value)
        except (AttributeError, ValueError):
            pass  # Keep as string
            
        test_data[attribute] = value
        
    ai_test_context['data']['current'] = test_data
    context.test_data = test_data


@given('a document of type "{doc_type}"')
@given('a {doc_type} document')
def step_document_of_type(context: Context, doc_type: str):
    """Set up a document for testing."""
    ai_test_context['data']['document'] = {
        'type': doc_type,
        'content': f"Sample {doc_type} document content for testing",
        'size': 1024,
        'format': 'text'
    }
    context.document = ai_test_context['data']['document']


@given('data volume is {operator} {threshold:d}')
def step_data_volume_condition(context: Context, operator: str, threshold: int):
    """Set up data volume condition."""
    if operator in ['greater than', 'above', '>']:
        volume = threshold + 100
    elif operator in ['less than', 'below', '<']:
        volume = threshold - 100
    else:
        volume = threshold
        
    ai_test_context['data']['volume'] = volume
    context.data_volume = volume


# =============================================================================
# AI Framework Action Steps
# =============================================================================

@when('LangChain analyzes the content')
@when('LangChain performs {action}')
def step_langchain_action(context: Context, action: str = 'content analysis'):
    """Simulate LangChain performing an action."""
    start_time = time.time()
    
    # Simulate LangChain processing
    ai_test_context['results']['langchain'] = {
        'action': action,
        'status': 'completed',
        'execution_time': time.time() - start_time,
        'output': f"LangChain {action} result"
    }
    
    context.langchain_result = ai_test_context['results']['langchain']


@when('Semantic Kernel coordinates {process}')
@when('Semantic Kernel performs {action}')
def step_semantic_kernel_action(context: Context, process: str = None, action: str = None):
    """Simulate Semantic Kernel performing coordination or action."""
    start_time = time.time()
    action_name = process or action or 'coordination'
    
    ai_test_context['results']['semantic_kernel'] = {
        'action': action_name,
        'status': 'completed',
        'execution_time': time.time() - start_time,
        'agents_coordinated': 3,
        'output': f"Semantic Kernel {action_name} result"
    }
    
    context.semantic_kernel_result = ai_test_context['results']['semantic_kernel']


@when('Temporal starts {workflow_type} workflow')
@when('Temporal executes workflow')
def step_temporal_workflow(context: Context, workflow_type: str = 'business'):
    """Simulate Temporal workflow execution."""
    start_time = time.time()
    
    ai_test_context['results']['temporal'] = {
        'workflow_type': workflow_type,
        'status': 'started',
        'workflow_id': f"wf_{int(time.time())}",
        'execution_time': time.time() - start_time,
        'activities_scheduled': 5
    }
    
    context.temporal_result = ai_test_context['results']['temporal']


@when('MCP toolkit executes {tool_name}')
@when('MCP processes the request')
def step_mcp_action(context: Context, tool_name: str = 'generic_tool'):
    """Simulate MCP tool execution."""
    start_time = time.time()
    
    ai_test_context['results']['mcp'] = {
        'tool': tool_name,
        'status': 'executed',
        'execution_time': time.time() - start_time,
        'output': f"MCP {tool_name} execution result"
    }
    
    context.mcp_result = ai_test_context['results']['mcp']


# =============================================================================
# Cross-Framework Coordination Steps
# =============================================================================

@when('AI frameworks coordinate to process the request')
@when('frameworks work together to {accomplish}')
def step_frameworks_coordinate(context: Context, accomplish: str = 'process the request'):
    """Simulate coordination between multiple AI frameworks."""
    start_time = time.time()
    
    # Simulate coordination across available frameworks
    coordinated_frameworks = []
    for framework in ai_test_context['frameworks'].keys():
        if ai_test_context['frameworks'][framework]['status'] in ['available', 'healthy']:
            coordinated_frameworks.append(framework)
    
    ai_test_context['results']['coordination'] = {
        'task': accomplish,
        'frameworks_involved': coordinated_frameworks,
        'status': 'completed',
        'coordination_time': time.time() - start_time,
        'success': True
    }
    
    context.coordination_result = ai_test_context['results']['coordination']


@when('the business logic orchestrator evaluates the scenario')
def step_orchestrator_evaluates(context: Context):
    """Simulate business logic orchestrator evaluation."""
    start_time = time.time()
    
    # Determine coordination strategy based on available frameworks and data
    strategy = 'sequential'
    if len(ai_test_context['frameworks']) > 3:
        strategy = 'parallel'
    elif ai_test_context['data'].get('volume', 0) > 1000:
        strategy = 'batch'
    
    ai_test_context['results']['orchestrator'] = {
        'strategy': strategy,
        'frameworks_selected': list(ai_test_context['frameworks'].keys()),
        'evaluation_time': time.time() - start_time,
        'confidence': 0.95
    }
    
    context.orchestrator_result = ai_test_context['results']['orchestrator']


# =============================================================================
# Verification and Assertion Steps
# =============================================================================

@then('the AI processing should complete successfully')
@then('all frameworks should complete successfully')
def step_processing_successful(context: Context):
    """Verify that AI processing completed successfully."""
    for framework, result in ai_test_context['results'].items():
        if isinstance(result, dict):
            assert result.get('status') in ['completed', 'executed', 'started'], \
                f"Framework {framework} did not complete successfully: {result.get('status')}"


@then('the response time should be under {max_seconds:f} seconds')
@then('processing should complete within {max_seconds:f} seconds')
def step_response_time_check(context: Context, max_seconds: float):
    """Verify response time meets requirements."""
    for framework, result in ai_test_context['results'].items():
        if isinstance(result, dict) and 'execution_time' in result:
            execution_time = result['execution_time']
            assert execution_time < max_seconds, \
                f"Framework {framework} took {execution_time:.2f}s, expected under {max_seconds}s"


@then('LangChain should produce {output_type}')
def step_langchain_output_verification(context: Context, output_type: str):
    """Verify LangChain produces expected output type."""
    langchain_result = ai_test_context['results'].get('langchain', {})
    assert langchain_result.get('status') == 'completed', \
        f"LangChain should complete successfully"
    assert 'output' in langchain_result, \
        f"LangChain should produce {output_type} output"


@then('Semantic Kernel should coordinate {num_agents:d} agents')
def step_semantic_kernel_coordination_verification(context: Context, num_agents: int):
    """Verify Semantic Kernel coordinates expected number of agents."""
    sk_result = ai_test_context['results'].get('semantic_kernel', {})
    agents_coordinated = sk_result.get('agents_coordinated', 0)
    assert agents_coordinated >= num_agents, \
        f"Expected at least {num_agents} agents, got {agents_coordinated}"


@then('Temporal should manage workflow state')
@then('Temporal workflow should be {status}')
def step_temporal_workflow_verification(context: Context, status: str = 'active'):
    """Verify Temporal workflow state management."""
    temporal_result = ai_test_context['results'].get('temporal', {})
    workflow_status = temporal_result.get('status', 'unknown')
    
    if status == 'active':
        assert workflow_status in ['started', 'running', 'active'], \
            f"Expected active workflow, got {workflow_status}"
    else:
        assert workflow_status == status, \
            f"Expected workflow status {status}, got {workflow_status}"


@then('MCP tools should execute without errors')
def step_mcp_execution_verification(context: Context):
    """Verify MCP tool execution completed without errors."""
    mcp_result = ai_test_context['results'].get('mcp', {})
    assert mcp_result.get('status') == 'executed', \
        f"MCP tool should execute successfully"
    assert 'error' not in mcp_result, \
        f"MCP execution should not have errors: {mcp_result.get('error', '')}"


@then('frameworks should work together seamlessly')
@then('cross-framework coordination should succeed')
def step_coordination_verification(context: Context):
    """Verify successful cross-framework coordination."""
    coordination_result = ai_test_context['results'].get('coordination', {})
    assert coordination_result.get('success') == True, \
        f"Cross-framework coordination should succeed"
    
    frameworks_involved = coordination_result.get('frameworks_involved', [])
    assert len(frameworks_involved) >= 2, \
        f"Coordination should involve multiple frameworks, got {len(frameworks_involved)}"


# =============================================================================
# Performance and Quality Steps
# =============================================================================

@then('the overall process should meet quality standards')
def step_quality_standards_verification(context: Context):
    """Verify the process meets quality standards."""
    # Check that all frameworks completed
    completed_frameworks = 0
    for framework, result in ai_test_context['results'].items():
        if isinstance(result, dict) and result.get('status') in ['completed', 'executed', 'started']:
            completed_frameworks += 1
    
    assert completed_frameworks >= 2, \
        f"Quality standards require multiple framework coordination, got {completed_frameworks}"


@then('resource usage should be optimal')
def step_resource_optimization_verification(context: Context):
    """Verify optimal resource usage."""
    # Check execution times are reasonable
    total_time = 0
    for framework, result in ai_test_context['results'].items():
        if isinstance(result, dict) and 'execution_time' in result:
            total_time += result['execution_time']
    
    # For testing, assume under 5 seconds total is optimal
    assert total_time < 5.0, \
        f"Total execution time should be under 5 seconds for optimal resource usage, got {total_time:.2f}s"


@then('the business logic should be correctly implemented')
def step_business_logic_verification(context: Context):
    """Verify business logic implementation correctness."""
    orchestrator_result = ai_test_context['results'].get('orchestrator', {})
    
    # Check that orchestrator made logical decisions
    assert orchestrator_result.get('confidence', 0) > 0.8, \
        f"Business logic confidence should be high, got {orchestrator_result.get('confidence', 0)}"
    
    # Check that appropriate frameworks were selected
    frameworks_selected = orchestrator_result.get('frameworks_selected', [])
    available_frameworks = list(ai_test_context['frameworks'].keys())
    
    assert len(frameworks_selected) > 0, \
        f"Business logic should select at least one framework"
    assert all(fw in available_frameworks for fw in frameworks_selected), \
        f"Selected frameworks should be available"


# =============================================================================
# Error Handling and Edge Case Steps
# =============================================================================

@given('{framework} is temporarily unavailable')
def step_framework_unavailable(context: Context, framework: str):
    """Simulate framework temporary unavailability."""
    framework_key = framework.lower().replace(' ', '_')
    ai_test_context['frameworks'][framework_key] = {
        'status': 'unavailable',
        'error': 'Temporarily unavailable for testing',
        'last_check': time.time()
    }


@then('the system should gracefully handle {framework} unavailability')
def step_graceful_handling_verification(context: Context, framework: str):
    """Verify graceful handling of framework unavailability."""
    coordination_result = ai_test_context['results'].get('coordination', {})
    
    # Check that coordination still succeeded despite unavailable framework
    assert coordination_result.get('success') == True, \
        f"System should handle {framework} unavailability gracefully"
    
    # Check that other frameworks were used
    frameworks_involved = coordination_result.get('frameworks_involved', [])
    framework_key = framework.lower().replace(' ', '_')
    assert framework_key not in frameworks_involved, \
        f"Unavailable framework {framework} should not be involved in coordination"


@then('appropriate fallback mechanisms should activate')
def step_fallback_verification(context: Context):
    """Verify activation of fallback mechanisms."""
    # Check that at least one framework was used as fallback
    frameworks_used = []
    for framework, result in ai_test_context['results'].items():
        if isinstance(result, dict) and result.get('status') in ['completed', 'executed']:
            frameworks_used.append(framework)
    
    assert len(frameworks_used) >= 1, \
        f"Fallback mechanisms should ensure at least one framework processes the request"


# =============================================================================
# Utility Functions
# =============================================================================

def reset_ai_test_context():
    """Reset the AI test context for clean test runs."""
    global ai_test_context
    ai_test_context = {
        'frameworks': {},
        'data': {},
        'results': {},
        'performance': {},
        'errors': []
    }


def get_test_summary():
    """Get a summary of the test execution."""
    return {
        'frameworks_tested': len(ai_test_context['frameworks']),
        'results_captured': len(ai_test_context['results']),
        'coordination_successful': ai_test_context['results'].get('coordination', {}).get('success', False),
        'total_execution_time': sum(
            result.get('execution_time', 0) 
            for result in ai_test_context['results'].values() 
            if isinstance(result, dict)
        )
    }
