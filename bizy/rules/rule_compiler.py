"""
Rule Compiler: Compiles and optimizes business rules for execution.

This module provides compilation and optimization capabilities for business rules,
including dependency analysis, execution planning, and performance optimization.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx

from ..core.business_rule import BusinessRule, RuleCondition, RuleAction

logger = logging.getLogger(__name__)


@dataclass
class CompiledRule:
    """Compiled and optimized rule representation."""
    rule: BusinessRule
    execution_plan: List[List[RuleAction]]  # Actions grouped by execution stage
    dependencies: Dict[str, Set[str]]  # Action dependencies
    condition_tree: Dict[str, Any]  # Optimized condition evaluation tree
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_optimized(self) -> bool:
        """Check if rule has been optimized."""
        return self.metadata.get("optimized", False)


@dataclass
class CompilationResult:
    """Result of rule compilation."""
    compiled_rule: Optional[CompiledRule]
    success: bool
    errors: List[str]
    warnings: List[str]
    optimization_stats: Dict[str, Any] = field(default_factory=dict)


class RuleCompiler:
    """
    Compiles business rules for optimal execution.
    
    Features:
    - Dependency analysis and resolution
    - Execution plan generation
    - Condition optimization
    - Performance analysis
    - Rule composition and inheritance
    """
    
    def __init__(self):
        self.compilation_cache: Dict[str, CompiledRule] = {}
        self.optimization_strategies = {
            "condition_simplification": self._optimize_conditions,
            "action_parallelization": self._optimize_action_parallelization,
            "common_subexpression_elimination": self._optimize_common_subexpressions,
            "dead_code_elimination": self._optimize_dead_code
        }
        
    def compile(
        self,
        rule: BusinessRule,
        optimization_level: int = 2
    ) -> CompilationResult:
        """
        Compile a business rule.
        
        Args:
            rule: Rule to compile
            optimization_level: 0=none, 1=basic, 2=full, 3=aggressive
            
        Returns:
            CompilationResult with compiled rule
        """
        errors = []
        warnings = []
        optimization_stats = {}
        
        try:
            # Check cache
            cache_key = f"{rule.id}_{optimization_level}"
            if cache_key in self.compilation_cache:
                return CompilationResult(
                    compiled_rule=self.compilation_cache[cache_key],
                    success=True,
                    errors=[],
                    warnings=[],
                    optimization_stats={"cache_hit": True}
                )
                
            # Analyze dependencies
            dependencies = self._analyze_dependencies(rule)
            
            # Build condition tree
            condition_tree = self._build_condition_tree(rule.conditions)
            
            # Generate initial execution plan
            execution_plan = self._generate_execution_plan(rule.actions, dependencies)
            
            # Create compiled rule
            compiled_rule = CompiledRule(
                rule=rule,
                execution_plan=execution_plan,
                dependencies=dependencies,
                condition_tree=condition_tree,
                metadata={
                    "optimization_level": optimization_level,
                    "compiled_at": self._get_timestamp()
                }
            )
            
            # Apply optimizations
            if optimization_level > 0:
                compiled_rule, opt_stats = self._apply_optimizations(
                    compiled_rule, optimization_level
                )
                optimization_stats.update(opt_stats)
                
            # Validate compiled rule
            validation_errors = self._validate_compiled_rule(compiled_rule)
            errors.extend(validation_errors)
            
            if not errors:
                # Cache successful compilation
                self.compilation_cache[cache_key] = compiled_rule
                
                return CompilationResult(
                    compiled_rule=compiled_rule,
                    success=True,
                    errors=errors,
                    warnings=warnings,
                    optimization_stats=optimization_stats
                )
            else:
                return CompilationResult(
                    compiled_rule=None,
                    success=False,
                    errors=errors,
                    warnings=warnings,
                    optimization_stats=optimization_stats
                )
                
        except Exception as e:
            logger.error(f"Error compiling rule {rule.id}: {e}")
            return CompilationResult(
                compiled_rule=None,
                success=False,
                errors=[str(e)],
                warnings=warnings,
                optimization_stats=optimization_stats
            )
            
    def _analyze_dependencies(self, rule: BusinessRule) -> Dict[str, Set[str]]:
        """Analyze action dependencies."""
        dependencies = defaultdict(set)
        
        # Analyze explicit dependencies
        for action in rule.actions:
            if action.depends_on:
                dependencies[action.action].update(action.depends_on)
                
        # Analyze implicit dependencies based on parameters
        action_outputs = {}
        
        for i, action in enumerate(rule.actions):
            # Track potential outputs
            if "output_field" in action.parameters:
                output_field = action.parameters["output_field"]
                action_outputs[output_field] = action.action
                
            # Check for input dependencies
            for param_name, param_value in action.parameters.items():
                if isinstance(param_value, str) and param_value.startswith("${"):
                    # Parameter references another field
                    field_name = param_value[2:-1]  # Remove ${ and }
                    
                    # Check if field is produced by another action
                    if field_name in action_outputs:
                        dependencies[action.action].add(action_outputs[field_name])
                        
        return dict(dependencies)
        
    def _build_condition_tree(self, conditions: List[RuleCondition]) -> Dict[str, Any]:
        """Build optimized condition evaluation tree."""
        if not conditions:
            return {"type": "empty", "result": True}
            
        # Group by combinator
        groups = defaultdict(list)
        for condition in conditions:
            combinator = condition.combinator or "all"
            groups[combinator].append(condition)
            
        # Build tree structure
        tree = {
            "type": "root",
            "groups": []
        }
        
        for combinator, group_conditions in groups.items():
            group_node = {
                "type": "group",
                "combinator": combinator,
                "conditions": []
            }
            
            # Sort conditions for optimal evaluation order
            sorted_conditions = self._sort_conditions_by_cost(group_conditions)
            
            for condition in sorted_conditions:
                condition_node = {
                    "type": "condition",
                    "field": condition.field,
                    "operator": condition.operator,
                    "value": condition.value,
                    "cost": self._estimate_condition_cost(condition)
                }
                group_node["conditions"].append(condition_node)
                
            tree["groups"].append(group_node)
            
        return tree
        
    def _generate_execution_plan(
        self,
        actions: List[RuleAction],
        dependencies: Dict[str, Set[str]]
    ) -> List[List[RuleAction]]:
        """Generate execution plan with parallelization."""
        # Build dependency graph
        graph = nx.DiGraph()
        
        # Add nodes
        for action in actions:
            graph.add_node(action.action, data=action)
            
        # Add edges
        for action_name, deps in dependencies.items():
            for dep in deps:
                if graph.has_node(dep):
                    graph.add_edge(dep, action_name)
                    
        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")
            
        # Generate execution stages using topological sort
        execution_plan = []
        
        if graph.nodes():
            # Get topological generations (parallel groups)
            for generation in nx.topological_generations(graph):
                stage = [graph.nodes[node]["data"] for node in generation]
                execution_plan.append(stage)
        else:
            # No dependencies, all actions can run in parallel
            execution_plan = [actions]
            
        return execution_plan
        
    def _apply_optimizations(
        self,
        compiled_rule: CompiledRule,
        optimization_level: int
    ) -> Tuple[CompiledRule, Dict[str, Any]]:
        """Apply optimization strategies."""
        stats = {"original_actions": len(compiled_rule.rule.actions)}
        
        # Select optimization strategies based on level
        if optimization_level == 1:
            strategies = ["condition_simplification"]
        elif optimization_level == 2:
            strategies = ["condition_simplification", "action_parallelization"]
        else:  # level 3+
            strategies = list(self.optimization_strategies.keys())
            
        # Apply selected strategies
        for strategy_name in strategies:
            if strategy_name in self.optimization_strategies:
                strategy = self.optimization_strategies[strategy_name]
                compiled_rule, strategy_stats = strategy(compiled_rule)
                stats[strategy_name] = strategy_stats
                
        compiled_rule.metadata["optimized"] = True
        stats["final_actions"] = len(compiled_rule.rule.actions)
        
        return compiled_rule, stats
        
    def _optimize_conditions(
        self,
        compiled_rule: CompiledRule
    ) -> Tuple[CompiledRule, Dict[str, Any]]:
        """Optimize condition evaluation."""
        stats = {"simplified_conditions": 0}
        
        # Simplify condition tree
        tree = compiled_rule.condition_tree
        
        for group in tree.get("groups", []):
            if group["combinator"] == "all":
                # Remove always-true conditions
                original_count = len(group["conditions"])
                group["conditions"] = [
                    c for c in group["conditions"]
                    if not self._is_always_true(c)
                ]
                stats["simplified_conditions"] += original_count - len(group["conditions"])
                
            elif group["combinator"] == "any":
                # Remove always-false conditions
                original_count = len(group["conditions"])
                group["conditions"] = [
                    c for c in group["conditions"]
                    if not self._is_always_false(c)
                ]
                stats["simplified_conditions"] += original_count - len(group["conditions"])
                
        return compiled_rule, stats
        
    def _optimize_action_parallelization(
        self,
        compiled_rule: CompiledRule
    ) -> Tuple[CompiledRule, Dict[str, Any]]:
        """Optimize action parallelization."""
        stats = {
            "original_stages": len(compiled_rule.execution_plan),
            "parallel_actions": 0
        }
        
        # Reanalyze for better parallelization
        new_plan = []
        
        for stage in compiled_rule.execution_plan:
            # Check if actions in stage can be further parallelized
            if len(stage) > 1:
                stats["parallel_actions"] += len(stage)
                
            # Keep stage as is (already optimized in generation)
            new_plan.append(stage)
            
        compiled_rule.execution_plan = new_plan
        stats["final_stages"] = len(new_plan)
        
        return compiled_rule, stats
        
    def _optimize_common_subexpressions(
        self,
        compiled_rule: CompiledRule
    ) -> Tuple[CompiledRule, Dict[str, Any]]:
        """Eliminate common subexpressions in conditions."""
        stats = {"eliminated_subexpressions": 0}
        
        # Find common field accesses
        field_access_count = defaultdict(int)
        
        for group in compiled_rule.condition_tree.get("groups", []):
            for condition in group["conditions"]:
                field_access_count[condition["field"]] += 1
                
        # Mark fields accessed multiple times for caching
        for field, count in field_access_count.items():
            if count > 1:
                compiled_rule.metadata.setdefault("cache_fields", set()).add(field)
                stats["eliminated_subexpressions"] += count - 1
                
        return compiled_rule, stats
        
    def _optimize_dead_code(
        self,
        compiled_rule: CompiledRule
    ) -> Tuple[CompiledRule, Dict[str, Any]]:
        """Remove dead code (unreachable actions)."""
        stats = {"removed_actions": 0}
        
        # Analyze which actions produce unused outputs
        used_outputs = set()
        action_outputs = {}
        
        # First pass: collect outputs
        for stage in compiled_rule.execution_plan:
            for action in stage:
                if "output_field" in action.parameters:
                    action_outputs[action.action] = action.parameters["output_field"]
                    
        # Second pass: find used outputs
        for stage in compiled_rule.execution_plan:
            for action in stage:
                for param_value in action.parameters.values():
                    if isinstance(param_value, str) and param_value.startswith("${"):
                        field_name = param_value[2:-1]
                        used_outputs.add(field_name)
                        
        # Remove actions with unused outputs
        new_plan = []
        for stage in compiled_rule.execution_plan:
            new_stage = []
            for action in stage:
                if action.action in action_outputs:
                    output = action_outputs[action.action]
                    if output not in used_outputs:
                        stats["removed_actions"] += 1
                        continue
                new_stage.append(action)
                
            if new_stage:
                new_plan.append(new_stage)
                
        compiled_rule.execution_plan = new_plan
        
        return compiled_rule, stats
        
    def _validate_compiled_rule(self, compiled_rule: CompiledRule) -> List[str]:
        """Validate compiled rule for correctness."""
        errors = []
        
        # Check execution plan is not empty
        if not compiled_rule.execution_plan:
            errors.append("Execution plan is empty")
            
        # Check all actions are included
        all_actions = set(action.action for action in compiled_rule.rule.actions)
        planned_actions = set()
        
        for stage in compiled_rule.execution_plan:
            for action in stage:
                planned_actions.add(action.action)
                
        missing_actions = all_actions - planned_actions
        if missing_actions:
            errors.append(f"Actions missing from execution plan: {missing_actions}")
            
        # Verify dependency ordering
        executed = set()
        for stage in compiled_rule.execution_plan:
            for action in stage:
                deps = compiled_rule.dependencies.get(action.action, set())
                unmet_deps = deps - executed
                if unmet_deps:
                    errors.append(f"Action {action.action} has unmet dependencies: {unmet_deps}")
                    
            # Mark stage actions as executed
            for action in stage:
                executed.add(action.action)
                
        return errors
        
    def _sort_conditions_by_cost(self, conditions: List[RuleCondition]) -> List[RuleCondition]:
        """Sort conditions by evaluation cost for optimization."""
        return sorted(conditions, key=lambda c: self._estimate_condition_cost(c))
        
    def _estimate_condition_cost(self, condition: RuleCondition) -> float:
        """Estimate computational cost of evaluating a condition."""
        base_cost = 1.0
        
        # Operator costs
        operator_costs = {
            "equals": 1.0,
            "not_equals": 1.0,
            "greater_than": 1.0,
            "less_than": 1.0,
            "contains": 2.0,
            "starts_with": 1.5,
            "ends_with": 1.5,
            "regex": 5.0,
            "in": 2.0,
            "not_in": 2.0
        }
        
        cost = base_cost * operator_costs.get(condition.operator, 1.0)
        
        # Field access cost (nested fields are more expensive)
        field_depth = len(condition.field.split('.'))
        cost *= field_depth
        
        return cost
        
    def _is_always_true(self, condition_node: Dict[str, Any]) -> bool:
        """Check if condition always evaluates to true."""
        # Simple cases
        if condition_node["operator"] == "equals" and condition_node["value"] is True:
            return condition_node["field"] == "true"
        return False
        
    def _is_always_false(self, condition_node: Dict[str, Any]) -> bool:
        """Check if condition always evaluates to false."""
        # Simple cases
        if condition_node["operator"] == "equals" and condition_node["value"] is False:
            return condition_node["field"] == "true"
        return False
        
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
        
    def compose_rules(
        self,
        base_rule: BusinessRule,
        *additional_rules: BusinessRule,
        composition_type: str = "merge"
    ) -> BusinessRule:
        """
        Compose multiple rules into a single rule.
        
        Args:
            base_rule: Base rule to build upon
            additional_rules: Rules to compose with base
            composition_type: "merge", "override", or "extend"
            
        Returns:
            Composed BusinessRule
        """
        if composition_type == "merge":
            # Merge all rules into one
            composed = BusinessRule(
                id=f"composed_{base_rule.id}",
                name=f"Composed: {base_rule.name}",
                description=base_rule.description
            )
            
            # Merge conditions (AND between rules)
            for rule in [base_rule] + list(additional_rules):
                for condition in rule.conditions:
                    composed.add_condition(condition)
                    
            # Merge actions (preserving order)
            for rule in [base_rule] + list(additional_rules):
                for action in rule.actions:
                    composed.add_action(action)
                    
        elif composition_type == "override":
            # Later rules override earlier ones
            composed = BusinessRule(
                id=f"override_{base_rule.id}",
                name=base_rule.name,
                description=base_rule.description
            )
            
            # Start with base conditions/actions
            for condition in base_rule.conditions:
                composed.add_condition(condition)
            for action in base_rule.actions:
                composed.add_action(action)
                
            # Override with additional rules
            for rule in additional_rules:
                # Replace conditions if same field
                existing_fields = {c.field for c in composed.conditions}
                for condition in rule.conditions:
                    if condition.field in existing_fields:
                        # Remove old condition
                        composed.conditions = [
                            c for c in composed.conditions
                            if c.field != condition.field
                        ]
                    composed.add_condition(condition)
                    
                # Replace actions if same framework/action
                existing_actions = {(a.framework, a.action) for a in composed.actions}
                for action in rule.actions:
                    if (action.framework, action.action) in existing_actions:
                        # Remove old action
                        composed.actions = [
                            a for a in composed.actions
                            if not (a.framework == action.framework and a.action == action.action)
                        ]
                    composed.add_action(action)
                    
        elif composition_type == "extend":
            # Inherit from base, extend with additional
            composed = BusinessRule(
                id=f"extended_{base_rule.id}",
                name=f"Extended: {base_rule.name}",
                description=base_rule.description,
                metadata={
                    "parent_rule": base_rule.id,
                    "extensions": [r.id for r in additional_rules]
                }
            )
            
            # Copy base rule
            for condition in base_rule.conditions:
                composed.add_condition(condition)
            for action in base_rule.actions:
                composed.add_action(action)
                
            # Add extensions
            for rule in additional_rules:
                for condition in rule.conditions:
                    composed.add_condition(condition)
                for action in rule.actions:
                    composed.add_action(action)
                    
        return composed
        
    def clear_cache(self):
        """Clear compilation cache."""
        self.compilation_cache.clear()