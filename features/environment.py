"""
Behave environment configuration for Business Logic Orchestrator BDD testing.

This module sets up the testing environment and provides hooks for
scenario execution and cleanup with the existing orchestration system.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from business_logic_orchestrator.core.meta_orchestrator import MetaOrchestrator
from business_logic_orchestrator.bdd.scenario_executor import BDDScenarioExecutor
from business_logic_orchestrator.events import EventBus

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def before_all(context):
    """Set up global test environment before all scenarios."""
    print("🚀 Starting Business Logic Orchestrator BDD Tests")
    
    # Set up async event loop for testing
    if not hasattr(context, 'loop'):
        context.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(context.loop)
    
    # Initialize global test components
    context.global_orchestrator = None
    context.global_bdd_executor = None
    
    # Test configuration
    context.test_config = {
        'timeout': 30,
        'retry_count': 3,
        'log_level': 'INFO'
    }


def before_feature(context, feature):
    """Set up environment before each feature."""
    print(f"📁 Starting feature: {feature.name}")
    
    # Feature-specific setup can be added here
    context.feature_start_time = asyncio.get_event_loop().time()


def before_scenario(context, scenario):
    """Set up environment before each scenario."""
    print(f"📋 Starting scenario: {scenario.name}")
    
    # Create fresh orchestrator for each scenario to ensure isolation
    context.event_bus = EventBus()
    context.orchestrator = MetaOrchestrator(context.event_bus)
    context.bdd_executor = BDDScenarioExecutor(context.orchestrator)
    
    # Reset scenario-specific state
    context.execution_results = {}
    context.performance_metrics = {}
    context.scenario_start_time = asyncio.get_event_loop().time()
    
    # Set up test data containers
    context.customers = {}
    context.tasks = {}
    context.frameworks = {}
    context.events = []


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    scenario_duration = asyncio.get_event_loop().time() - context.scenario_start_time
    
    if scenario.status == "passed":
        print(f"✅ Scenario passed: {scenario.name} ({scenario_duration:.2f}s)")
    else:
        print(f"❌ Scenario failed: {scenario.name} ({scenario_duration:.2f}s)")
        
        # Log failure details for debugging
        if hasattr(context, 'execution_results'):
            logger.error(f"Execution results: {context.execution_results}")
        
        # Log any errors from the scenario
        for step in scenario.steps:
            if step.status == "failed":
                logger.error(f"Failed step: {step.name}")
                if hasattr(step, 'exception'):
                    logger.error(f"Exception: {step.exception}")
    
    # Clean up resources
    if hasattr(context, 'orchestrator') and context.orchestrator:
        # In a real implementation, this would clean up adapter connections
        # For now, we just clear references
        context.orchestrator = None
        context.bdd_executor = None


def after_feature(context, feature):
    """Clean up after each feature."""
    feature_duration = asyncio.get_event_loop().time() - context.feature_start_time
    
    passed_scenarios = len([s for s in feature.scenarios if s.status == "passed"])
    total_scenarios = len(feature.scenarios)
    
    print(f"📊 Feature complete: {feature.name}")
    print(f"    Scenarios: {passed_scenarios}/{total_scenarios} passed ({feature_duration:.2f}s)")


def after_all(context):
    """Clean up global test environment after all scenarios."""
    # Close event loop
    if hasattr(context, 'loop'):
        try:
            context.loop.close()
        except Exception as e:
            logger.warning(f"Error closing event loop: {e}")
    
    print("🏁 Business Logic Orchestrator BDD Tests Complete")


# Behave configuration hooks
def before_step(context, step):
    """Before each step execution."""
    # Optional: Add step-level logging or setup
    pass


def after_step(context, step):
    """After each step execution."""
    if step.status == "failed":
        print(f"💥 Step failed: {step.name}")
        
        # Capture debug information
        if hasattr(context, 'orchestrator'):
            # Log orchestrator state
            logger.error("Orchestrator state at failure:")
            logger.error(f"  Registered adapters: {list(context.orchestrator.adapters.keys())}")
            
        # Log any available test context
        test_data = {}
        if hasattr(context, 'customers'):
            test_data['customers'] = context.customers
        if hasattr(context, 'tasks'):
            test_data['tasks'] = context.tasks
        if hasattr(context, 'frameworks'):
            test_data['frameworks'] = context.frameworks
            
        if test_data:
            logger.error(f"Test context: {test_data}")


# Tag-based hooks for different test types
def before_tag(context, tag):
    """Handle tag-specific setup."""
    if tag == "integration":
        # Set up for integration tests
        context.test_mode = "integration"
        print("🔗 Running integration test")
    elif tag == "smoke":
        # Set up for smoke tests
        context.test_mode = "smoke"
        print("💨 Running smoke test")
    elif tag == "cross_framework":
        # Set up for cross-framework tests
        context.test_mode = "cross_framework"
        print("🌐 Running cross-framework test")


def after_tag(context, tag):
    """Handle tag-specific cleanup."""
    # Tag-specific cleanup can be added here
    pass
