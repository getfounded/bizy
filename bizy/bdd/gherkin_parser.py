"""
Gherkin Rule Parser: Converts Gherkin scenarios to BusinessRule objects.

This module parses Gherkin feature files and converts scenarios into executable
BusinessRule objects that can be processed by the MetaOrchestrator.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import yaml
from pathlib import Path

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction, RuleType, RulePriority


class GherkinRuleParser:
    """
    Parses Gherkin scenarios into BusinessRule objects.
    
    Converts natural language business scenarios into executable business rules
    that can be coordinated across multiple AI frameworks.
    """
    
    def __init__(self):
        self.framework_mappings = {
            'langchain': 'langchain',
            'semantic_kernel': 'semantic_kernel', 
            'mcp_toolkit': 'mcp',
            'mcp toolkit': 'mcp',
            'temporal': 'temporal',
            'fastmcp': 'fastmcp',
            'zep': 'zep'
        }
        
        # Condition parsing patterns
        self.condition_patterns = [
            # Customer attributes: "a customer with tier 'premium'"
            (r'customer with (\w+) ["\']([^"\']+)["\']', 
             lambda m: RuleCondition(f"customer.{m.group(1)}", "eq", m.group(2))),
            
            # Numeric comparisons: "sentiment score is below 0.3"
            (r'(\w+(?:\s+\w+)*)\s+(?:score\s+)?is below ([\d.]+)', 
             lambda m: RuleCondition(f"{m.group(1).replace(' ', '_')}_score", "lt", float(m.group(2)))),
            
            (r'(\w+(?:\s+\w+)*)\s+(?:score\s+)?is above ([\d.]+)', 
             lambda m: RuleCondition(f"{m.group(1).replace(' ', '_')}_score", "gt", float(m.group(2)))),
             
            # Direct equality: "processing_required equals true"
            (r'(\w+(?:\s+\w+)*)\s+equals? ["\']?([^"\']+)["\']?', 
             lambda m: RuleCondition(m.group(1).replace(' ', '_'), "eq", m.group(2))),
             
            # Data size comparisons: "data size is greater than 100"
            (r'(\w+(?:\s+\w+)*)\s+is (?:greater than|above) ([\d.]+)', 
             lambda m: RuleCondition(m.group(1).replace(' ', '_'), "gt", float(m.group(2)))),
             
            # Boolean conditions: "extract_knowledge is true"
            (r'(\w+(?:\s+\w+)*)\s+is (true|false)', 
             lambda m: RuleCondition(m.group(1).replace(' ', '_'), "eq", m.group(2).lower() == 'true')),
        ]
        
        # Action parsing patterns
        self.action_patterns = [
            # Via framework: "escalate to account manager via MCP toolkit"
            (r'(\w+(?:\s+\w+)*?)\s+via\s+(\w+(?:\s+\w+)*)', 
             lambda m: RuleAction(
                framework=self._normalize_framework(m.group(2)),
                action=m.group(1).lower().replace(' ', '_'),
                parameters={}
            )),
            
            # Should action using framework: "should analyze document using LangChain"
            (r'should\s+(\w+(?:\s+\w+)*?)\s+using\s+(\w+(?:\s+\w+)*)', 
             lambda m: RuleAction(
                framework=self._normalize_framework(m.group(2)),
                action=m.group(1).lower().replace(' ', '_'),
                parameters={}
            )),
            
            # Framework should action: "LangChain should extract contract terms"
            (r'(\w+(?:\s+\w+)*?)\s+should\s+(\w+(?:\s+\w+)*)', 
             lambda m: RuleAction(
                framework=self._normalize_framework(m.group(1)),
                action=m.group(2).lower().replace(' ', '_'),
                parameters={}
            )),
            
            # Direct action specification: "start priority workflow via Temporal"
            (r'(start|create|execute|run|analyze)\s+(\w+(?:\s+\w+)*?)\s+via\s+(\w+(?:\s+\w+)*)', 
             lambda m: RuleAction(
                framework=self._normalize_framework(m.group(3)),
                action=f"{m.group(1)}_{m.group(2).replace(' ', '_')}",
                parameters={}
            )),
        ]
        
    def _normalize_framework(self, framework_text: str) -> str:
        """Normalize framework name to standard mapping."""
        normalized = framework_text.lower().strip()
        return self.framework_mappings.get(normalized, normalized)
        
    def parse_feature_file(self, feature_path: Path) -> List[BusinessRule]:
        """Parse a Gherkin feature file into business rules."""
        rules = []
        
        with open(feature_path, 'r') as f:
            content = f.read()
            
        scenarios = self._extract_scenarios(content)
        
        for scenario in scenarios:
            rule = self._scenario_to_rule(scenario)
            if rule:
                rules.append(rule)
                
        return rules
        
    def parse_scenario_text(self, scenario_text: str) -> Optional[BusinessRule]:
        """Parse a single Gherkin scenario from text."""
        scenario = self._parse_scenario_block(scenario_text)
        return self._scenario_to_rule(scenario) if scenario else None
        
    def _extract_scenarios(self, content: str) -> List[Dict[str, Any]]:
        """Extract individual scenarios from feature file content."""
        scenarios = []
        
        # Split by scenario headers
        scenario_blocks = re.split(r'\n\s*Scenario(?:\s+Outline)?:', content)
        
        for block in scenario_blocks[1:]:  # Skip feature header
            scenario = self._parse_scenario_block(block)
            if scenario:
                scenarios.append(scenario)
                
        return scenarios
        
    def _parse_scenario_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single scenario block."""
        lines = block.strip().split('\n')
        if not lines:
            return None
            
        scenario_name = lines[0].strip()
        
        scenario = {
            'name': scenario_name,
            'steps': [],
            'examples': []
        }
        
        current_section = 'steps'
        current_table = []
        
        for line in lines[1:]:
            line = line.strip()
            
            if not line:
                continue
                
            if line.startswith('Examples:'):
                current_section = 'examples'
                continue
            elif line.startswith('|') and current_section == 'examples':
                scenario['examples'].append(self._parse_table_row(line))
            elif line.startswith(('Given', 'When', 'Then', 'And', 'But')):
                # Check if previous step had a table
                if current_table and scenario['steps']:
                    scenario['steps'][-1]['table'] = current_table
                    current_table = []
                    
                scenario['steps'].append(self._parse_step(line))
                current_section = 'steps'
            elif line.startswith('|') and current_section == 'steps':
                current_table.append(self._parse_table_row(line))
                
        # Handle final table
        if current_table and scenario['steps']:
            scenario['steps'][-1]['table'] = current_table
            
        return scenario
        
    def _parse_step(self, step_line: str) -> Dict[str, Any]:
        """Parse a single Gherkin step."""
        parts = step_line.split(' ', 1)
        keyword = parts[0]
        text = parts[1] if len(parts) > 1 else ''
        
        return {
            'keyword': keyword,
            'text': text,
            'table': []
        }
        
    def _parse_table_row(self, row: str) -> List[str]:
        """Parse a table row from Gherkin."""
        return [cell.strip() for cell in row.split('|')[1:-1]]
        
    def _scenario_to_rule(self, scenario: Dict[str, Any]) -> Optional[BusinessRule]:
        """Convert a Gherkin scenario to a BusinessRule object."""
        if not scenario or not scenario.get('steps'):
            return None
            
        rule_name = scenario['name']
        conditions = []
        actions = []
        
        # Parse steps for conditions and actions
        for step in scenario['steps']:
            if step['keyword'] in ['Given', 'And']:
                # Parse conditions from Given/And steps
                condition = self._parse_condition(step['text'])
                if condition:
                    conditions.append(condition)
                    
                # Handle table data for conditions
                if step.get('table'):
                    table_conditions = self._parse_condition_table(step['table'])
                    conditions.extend(table_conditions)
                    
            elif step['keyword'] in ['Then', 'And']:
                # Parse actions from Then/And steps
                action = self._parse_action(step['text'])
                if action:
                    actions.append(action)
                    
                # Handle table data for actions
                if step.get('table'):
                    table_actions = self._parse_action_table(step['table'])
                    actions.extend(table_actions)
                    
        if not actions:
            return None
            
        # Determine rule priority based on keywords
        priority = self._determine_priority(rule_name, scenario['steps'])
        rule_type = self._determine_rule_type(scenario['steps'])
            
        return BusinessRule(
            name=rule_name,
            rule_type=rule_type,
            priority=priority,
            conditions=conditions,
            actions=actions,
            description=f"Generated from Gherkin scenario: {rule_name}",
            metadata={
                "source": "gherkin",
                "original_scenario": scenario
            }
        )
        
    def _parse_condition(self, text: str) -> Optional[RuleCondition]:
        """Parse a condition from Gherkin text."""
        for pattern, parser in self.condition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return parser(match)
                
        return None
        
    def _parse_action(self, text: str) -> Optional[RuleAction]:
        """Parse an action from Gherkin text."""
        for pattern, parser in self.action_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return parser(match)
                
        return None
        
    def _parse_condition_table(self, table: List[List[str]]) -> List[RuleCondition]:
        """Parse conditions from a Gherkin table."""
        conditions = []
        
        if not table or len(table) < 2:
            return conditions
            
        headers = table[0]
        
        # Handle attribute-value tables
        if len(headers) == 2 and 'attribute' in headers[0].lower():
            attr_idx = 0
            val_idx = 1
            
            for row in table[1:]:
                if len(row) >= 2:
                    attribute = row[attr_idx]
                    value = row[val_idx]
                    
                    # Try to convert to appropriate type
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string
                        
                    conditions.append(RuleCondition(attribute, "eq", value))
                    
        return conditions
        
    def _parse_action_table(self, table: List[List[str]]) -> List[RuleAction]:
        """Parse actions from a Gherkin table."""
        actions = []
        
        if not table or len(table) < 2:
            return actions
            
        headers = [h.lower() for h in table[0]]
        
        # Handle framework-action tables
        if 'framework' in headers and 'action' in headers:
            framework_idx = headers.index('framework')
            action_idx = headers.index('action')
            
            for row in table[1:]:
                if len(row) > max(framework_idx, action_idx):
                    framework = self._normalize_framework(row[framework_idx])
                    action = row[action_idx].lower().replace(' ', '_')
                    
                    # Extract additional parameters if present
                    parameters = {}
                    for i, header in enumerate(headers):
                        if header not in ['framework', 'action'] and i < len(row):
                            parameters[header] = row[i]
                            
                    actions.append(RuleAction(framework, action, parameters))
                    
        return actions
        
    def _determine_priority(self, rule_name: str, steps: List[Dict[str, Any]]) -> RulePriority:
        """Determine rule priority based on keywords."""
        rule_text = (rule_name + " " + " ".join(step['text'] for step in steps)).lower()
        
        if any(word in rule_text for word in ['critical', 'urgent', 'emergency', 'escalat']):
            return RulePriority.CRITICAL
        elif any(word in rule_text for word in ['high', 'premium', 'priority', 'important']):
            return RulePriority.HIGH
        elif any(word in rule_text for word in ['low', 'background', 'batch']):
            return RulePriority.LOW
        else:
            return RulePriority.MEDIUM
            
    def _determine_rule_type(self, steps: List[Dict[str, Any]]) -> RuleType:
        """Determine rule type based on step patterns."""
        step_text = " ".join(step['text'] for step in steps).lower()
        
        if any(word in step_text for word in ['workflow', 'process', 'orchestrat', 'coordinat']):
            return RuleType.WORKFLOW
        elif any(word in step_text for word in ['policy', 'govern', 'compliance', 'rule']):
            return RuleType.POLICY
        elif any(word in step_text for word in ['action', 'execute', 'perform', 'trigger']):
            return RuleType.ACTION
        else:
            return RuleType.CONDITION


class ScenarioTemplateGenerator:
    """Generates Gherkin scenario templates for common business patterns."""
    
    @staticmethod
    def generate_customer_service_template() -> str:
        """Generate customer service automation template."""
        return '''Feature: Customer Service Automation
  As a customer service manager
  I want automated escalation for unhappy premium customers
  So that we retain high-value accounts

  Scenario: Premium customer with negative sentiment
    Given a customer with tier "premium"
    And the customer sentiment score is below 0.3
    When a support interaction is created
    Then escalate to account manager via MCP toolkit
    And start priority workflow via Temporal
    And update customer context in Zep memory
'''

    @staticmethod
    def generate_document_processing_template() -> str:
        """Generate document processing template."""
        return '''Feature: Enterprise Document Processing
  As a compliance officer
  I want automated document analysis and routing
  So that legal reviews are comprehensive and timely

  Scenario: Legal document onboarding workflow
    Given a new enterprise customer
    And LangChain document analyzer is available
    And Temporal workflow engine is running
    When the customer uploads legal documents
    Then LangChain should extract contract terms
    And Temporal should orchestrate approval workflow
    And MCP toolkit should update enterprise systems
    And the workflow should complete within 5 minutes
'''

    @staticmethod
    def generate_data_pipeline_template() -> str:
        """Generate data processing pipeline template."""
        return '''Feature: Multi-Source Data Integration
  As a data analyst
  I want coordinated data processing across AI tools
  So that insights are accurate and timely

  Scenario: Large dataset processing pipeline
    Given data size is greater than 100
    And processing is required
    When the data pipeline is triggered
    Then FastMCP should batch process the data
    And MCP toolkit should transform the results
    And Zep should store processing context
    And all frameworks should coordinate successfully
'''
