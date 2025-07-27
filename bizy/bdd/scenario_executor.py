"""
BDD Scenario Executor: Executes Gherkin scenarios through the MetaOrchestrator.

This module provides the bridge between BDD scenarios and the business logic
orchestration system, enabling natural language business scenarios to be executed
across multiple AI frameworks.
"""

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from ..core.meta_orchestrator import MetaOrchestrator
from ..core.business_rule import BusinessRule
from .gherkin_parser import GherkinRuleParser

logger = logging.getLogger(__name__)


class BDDScenarioExecutor:
    """
    Executes business rules defined in BDD scenarios.
    
    Bridges the gap between natural language business requirements
    and technical framework execution through the MetaOrchestrator.
    """
    
    def __init__(self, orchestrator: MetaOrchestrator):
        self.orchestrator = orchestrator
        self.parser = GherkinRuleParser()
        self.execution_history: List[Dict[str, Any]] = []
        
    async def execute_feature_file(self, feature_path: Path, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute all scenarios in a feature file."""
        context = context or {}
        
        try:
            rules = self.parser.parse_feature_file(feature_path)
            return await self._execute_rules(rules, context, str(feature_path))
        except Exception as e:
            logger.error(f"Failed to execute feature file {feature_path}: {e}")
            return {
                'feature': feature_path.name,
                'success': False,
                'error': str(e),
                'scenarios_executed': 0
            }
        
    async def execute_scenario_text(self, scenario_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single scenario from text."""
        context = context or {}
        
        try:
            rule = self.parser.parse_scenario_text(scenario_text)
            if not rule:
                return {
                    'success': False,
                    'error': 'Failed to parse scenario text',
                    'scenarios_executed': 0
                }
                
            return await self._execute_rules([rule], context, "text_scenario")
        except Exception as e:
            logger.error(f"Failed to execute scenario text: {e}")
            return {
                'success': False,
                'error': str(e),
                'scenarios_executed': 0
            }
            
    async def execute_business_rule(self, rule: BusinessRule, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single business rule."""
        context = context or {}
        
        try:
            return await self._execute_scenario_rule(rule, context)
        except Exception as e:
            logger.error(f"Failed to execute business rule {rule.name}: {e}")
            return {
                'rule_name': rule.name,
                'success': False,
                'error': str(e),
                'skipped': False
            }
        
    async def _execute_rules(self, rules: List[BusinessRule], context: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Execute a list of business rules."""
        results = {
            'source': source,
            'scenarios_executed': 0,
            'scenarios_passed': 0,
            'scenarios_failed': 0,
            'scenarios_skipped': 0,
            'total_execution_time': 0,
            'details': []
        }
        
        start_time = asyncio.get_event_loop().time()
        
        for rule in rules:
            scenario_start = asyncio.get_event_loop().time()
            scenario_result = await self._execute_scenario_rule(rule, context)
            scenario_duration = asyncio.get_event_loop().time() - scenario_start
            
            results['scenarios_executed'] += 1
            scenario_result['execution_time'] = scenario_duration
            
            if scenario_result.get('skipped', False):
                results['scenarios_skipped'] += 1
            elif scenario_result.get('success', False):
                results['scenarios_passed'] += 1
            else:
                results['scenarios_failed'] += 1
                
            results['details'].append({
                'rule_name': rule.name,
                'rule_id': rule.id,
                'result': scenario_result
            })
            
        results['total_execution_time'] = asyncio.get_event_loop().time() - start_time
        results['success'] = results['scenarios_failed'] == 0
        
        # Store in execution history
        self.execution_history.append(results)
        
        return results
        
    async def _execute_scenario_rule(self, rule: BusinessRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single business rule derived from a scenario."""
        logger.info(f"Executing BDD scenario rule: {rule.name}")
        
        try:
            # Check if rule conditions are met
            if not rule.should_execute(context):
                logger.info(f"Rule {rule.name} conditions not met, skipping")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Conditions not met',
                    'conditions_evaluated': len(rule.conditions),
                    'actions_planned': len(rule.actions)
                }
                
            # Execute rule through orchestrator
            logger.info(f"Executing rule {rule.name} with {len(rule.actions)} actions")
            execution_result = await self.orchestrator.execute_rule(rule, context)
            
            # Analyze execution results
            success = self._analyze_execution_success(execution_result)
            
            result = {
                'success': success,
                'skipped': False,
                'conditions_evaluated': len(rule.conditions),
                'actions_executed': len(rule.actions),
                'frameworks_involved': list(execution_result.keys()),
                'execution_details': execution_result
            }
            
            if success:
                logger.info(f"Rule {rule.name} executed successfully")
            else:
                logger.warning(f"Rule {rule.name} execution had failures")
                
            return result
            
        except Exception as e:
            logger.error(f"Exception during rule execution: {e}")
            return {
                'success': False,
                'skipped': False,
                'error': str(e),
                'conditions_evaluated': len(rule.conditions),
                'actions_planned': len(rule.actions)
            }
            
    def _analyze_execution_success(self, execution_result: Dict[str, Any]) -> bool:
        """Analyze execution results to determine overall success."""
        if not execution_result:
            return False
            
        # Check if any adapter had errors
        for adapter_name, result in execution_result.items():
            if isinstance(result, dict) and 'error' in result:
                logger.warning(f"Adapter {adapter_name} reported error: {result['error']}")
                return False
                
        return True
        
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get execution history."""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()
        
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'total_scenarios': 0,
                'total_passed': 0,
                'total_failed': 0,
                'total_skipped': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0
            }
            
        total_executions = len(self.execution_history)
        total_scenarios = sum(h['scenarios_executed'] for h in self.execution_history)
        total_passed = sum(h['scenarios_passed'] for h in self.execution_history)
        total_failed = sum(h['scenarios_failed'] for h in self.execution_history)
        total_skipped = sum(h['scenarios_skipped'] for h in self.execution_history)
        total_time = sum(h['total_execution_time'] for h in self.execution_history)
        
        success_rate = (total_passed / total_scenarios * 100) if total_scenarios > 0 else 0
        avg_time = total_time / total_executions if total_executions > 0 else 0
        
        return {
            'total_executions': total_executions,
            'total_scenarios': total_scenarios,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'success_rate': round(success_rate, 2),
            'average_execution_time': round(avg_time, 3)
        }


class BDDTestRunner:
    """Test runner for BDD scenarios with reporting capabilities."""
    
    def __init__(self, executor: BDDScenarioExecutor):
        self.executor = executor
        
    async def run_feature_directory(self, features_dir: Path, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run all feature files in a directory."""
        context = context or {}
        
        feature_files = list(features_dir.glob("*.feature"))
        if not feature_files:
            return {
                'success': False,
                'error': f"No feature files found in {features_dir}",
                'features_executed': 0
            }
            
        results = {
            'features_executed': 0,
            'features_passed': 0,
            'features_failed': 0,
            'total_scenarios': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'feature_results': []
        }
        
        for feature_file in feature_files:
            try:
                feature_result = await self.executor.execute_feature_file(feature_file, context)
                results['features_executed'] += 1
                
                if feature_result.get('success', False):
                    results['features_passed'] += 1
                else:
                    results['features_failed'] += 1
                    
                results['total_scenarios'] += feature_result.get('scenarios_executed', 0)
                results['total_passed'] += feature_result.get('scenarios_passed', 0)
                results['total_failed'] += feature_result.get('scenarios_failed', 0)
                results['total_skipped'] += feature_result.get('scenarios_skipped', 0)
                
                results['feature_results'].append({
                    'feature_file': feature_file.name,
                    'result': feature_result
                })
                
            except Exception as e:
                logger.error(f"Failed to execute feature file {feature_file}: {e}")
                results['features_executed'] += 1
                results['features_failed'] += 1
                results['feature_results'].append({
                    'feature_file': feature_file.name,
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })
                
        results['success'] = results['features_failed'] == 0
        return results
        
    def generate_report(self, results: Dict[str, Any], output_file: Optional[Path] = None) -> str:
        """Generate a human-readable test report."""
        report_lines = [
            "BDD Scenario Execution Report",
            "=" * 40,
            "",
            f"Features Executed: {results.get('features_executed', 0)}",
            f"Features Passed: {results.get('features_passed', 0)}",
            f"Features Failed: {results.get('features_failed', 0)}",
            "",
            f"Total Scenarios: {results.get('total_scenarios', 0)}",
            f"Scenarios Passed: {results.get('total_passed', 0)}",
            f"Scenarios Failed: {results.get('total_failed', 0)}",
            f"Scenarios Skipped: {results.get('total_skipped', 0)}",
            "",
        ]
        
        # Add feature-by-feature details
        if 'feature_results' in results:
            report_lines.append("Feature Details:")
            report_lines.append("-" * 20)
            
            for feature_result in results['feature_results']:
                feature_name = feature_result['feature_file']
                feature_data = feature_result['result']
                
                status = "PASSED" if feature_data.get('success', False) else "FAILED"
                report_lines.append(f"{feature_name}: {status}")
                
                if 'scenarios_executed' in feature_data:
                    report_lines.append(f"  Scenarios: {feature_data['scenarios_executed']}")
                    report_lines.append(f"  Passed: {feature_data.get('scenarios_passed', 0)}")
                    report_lines.append(f"  Failed: {feature_data.get('scenarios_failed', 0)}")
                    
                if 'error' in feature_data:
                    report_lines.append(f"  Error: {feature_data['error']}")
                    
                report_lines.append("")
                
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
                
        return report_text
