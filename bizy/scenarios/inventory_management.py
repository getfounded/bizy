"""
Inventory Management Scenario.

Demonstrates automated inventory management across multiple locations
using predictive analytics and cross-framework coordination.
"""

from typing import Any, Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import math

from ..core.business_rule import (
    BusinessRule, RuleType, RulePriority, RuleCondition, RuleAction
)
from ..core.meta_orchestrator import MetaOrchestrator
from ..events import EventBus, EventType

logger = logging.getLogger(__name__)


class InventoryManagementScenario:
    """
    Implements sophisticated inventory management that coordinates:
    - FastMCP for real-time inventory calculations
    - Temporal for reorder workflows
    - LangChain for demand prediction
    - Zep for historical pattern storage
    - MCP for supplier integration
    - Semantic Kernel for supply chain coordination
    """
    
    def __init__(self, orchestrator: MetaOrchestrator, event_bus: EventBus):
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.rules: List[BusinessRule] = []
        self._create_inventory_rules()
        
    def _create_inventory_rules(self):
        """Create business rules for inventory management."""
        
        # Rule 1: Reorder Point Calculation
        reorder_point_rule = BusinessRule(
            name="calculate_reorder_point",
            rule_type=RuleType.CALCULATION,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition("product.status", "eq", "active"),
                RuleCondition("product.auto_reorder", "eq", True)
            ],
            actions=[
                # Calculate with FastMCP for performance
                RuleAction(
                    framework="fastmcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "reorder_calculator",
                        "use_cache": True,
                        "parameters": {
                            "formula": "daily_sales_avg * lead_time * safety_factor",
                            "safety_factor": 1.5
                        }
                    }
                ),
                # Store calculation in memory
                RuleAction(
                    framework="zep",
                    action="store_memory",
                    parameters={
                        "type": "inventory_calculation",
                        "metadata": {
                            "calculation_type": "reorder_point",
                            "timestamp": "${calculation_timestamp}"
                        }
                    }
                )
            ],
            description="Calculate dynamic reorder points based on sales patterns"
        )
        self.rules.append(reorder_point_rule)
        
        # Rule 2: Auto-Reorder Trigger
        auto_reorder_rule = BusinessRule(
            name="auto_reorder_trigger",
            rule_type=RuleType.WORKFLOW,
            priority=RulePriority.CRITICAL,
            conditions=[
                RuleCondition("current_inventory", "lte", "${reorder_threshold}"),
                RuleCondition("supplier.status", "eq", "active"),
                RuleCondition("product.discontinuation_date", "gt", "${current_date_plus_90}")
            ],
            actions=[
                # Start reorder workflow
                RuleAction(
                    framework="temporal",
                    action="start_workflow",
                    parameters={
                        "workflow_name": "purchase_order_workflow",
                        "workflow_id": "po_${product_id}_${timestamp}",
                        "parameters": {
                            "order_quantity": "${calculated_order_quantity}",
                            "priority": "${order_priority}"
                        }
                    }
                ),
                # Notify supply chain team
                RuleAction(
                    framework="semantic_kernel",
                    action="communicate_agent",
                    parameters={
                        "agent_id": "supply_chain_coordinator",
                        "message_type": "reorder_notification",
                        "urgency": "${order_urgency}"
                    }
                ),
                # Create purchase order via MCP
                RuleAction(
                    framework="mcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "purchase_order_creator",
                        "parameters": {
                            "supplier_id": "${supplier_id}",
                            "items": "${order_items}",
                            "delivery_date": "${requested_delivery_date}"
                        }
                    }
                )
            ],
            description="Automatically trigger reorders when inventory falls below threshold"
        )
        self.rules.append(auto_reorder_rule)
        
        # Rule 3: Demand Prediction
        demand_prediction_rule = BusinessRule(
            name="demand_prediction_analysis",
            rule_type=RuleType.ACTION,
            priority=RulePriority.MEDIUM,
            conditions=[
                RuleCondition("enable_predictive_analytics", "eq", True),
                RuleCondition("historical_data_months", "gte", 3)
            ],
            actions=[
                # Retrieve historical data
                RuleAction(
                    framework="zep",
                    action="retrieve_memory",
                    parameters={
                        "session_id": "inventory_history",
                        "time_range": {
                            "start": "${three_months_ago}",
                            "end": "${current_date}"
                        },
                        "types": ["sales", "inventory_level"]
                    }
                ),
                # Analyze with LangChain
                RuleAction(
                    framework="langchain",
                    action="run_agent",
                    parameters={
                        "agent_name": "demand_predictor",
                        "task": "Predict demand for next 30 days",
                        "tools": ["trend_analyzer", "seasonality_detector", "forecast_generator"]
                    }
                ),
                # Optimize with FastMCP
                RuleAction(
                    framework="fastmcp",
                    action="batch_execute",
                    parameters={
                        "executions": [
                            {
                                "tool_name": "forecast_optimizer",
                                "parameters": {"confidence_level": 0.95}
                            },
                            {
                                "tool_name": "scenario_planner",
                                "parameters": {"scenarios": ["best", "worst", "likely"]}
                            }
                        ],
                        "parallel": True
                    }
                )
            ],
            description="Predict future demand using historical patterns and AI"
        )
        self.rules.append(demand_prediction_rule)
        
        # Rule 4: Multi-Location Allocation
        allocation_rule = BusinessRule(
            name="multi_location_allocation",
            rule_type=RuleType.POLICY,
            priority=RulePriority.MEDIUM,
            conditions=[
                RuleCondition("location_count", "gt", 1),
                RuleCondition("allocation_needed", "eq", True)
            ],
            actions=[
                # Calculate optimal allocation
                RuleAction(
                    framework="fastmcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "allocation_optimizer",
                        "parameters": {
                            "method": "weighted_distribution",
                            "factors": ["historical_sales", "current_demand", "storage_capacity"]
                        }
                    }
                ),
                # Create transfer orders
                RuleAction(
                    framework="temporal",
                    action="start_workflow",
                    parameters={
                        "workflow_name": "inventory_transfer",
                        "workflow_id": "transfer_${batch_id}",
                        "parameters": {
                            "transfers": "${allocation_plan}"
                        }
                    }
                ),
                # Update inventory systems
                RuleAction(
                    framework="mcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "inventory_updater",
                        "parameters": {
                            "updates": "${inventory_adjustments}",
                            "reason": "allocation_optimization"
                        }
                    }
                )
            ],
            description="Optimize inventory allocation across multiple locations"
        )
        self.rules.append(allocation_rule)
        
        # Rule 5: Seasonal Adjustment
        seasonal_adjustment_rule = BusinessRule(
            name="seasonal_inventory_adjustment",
            rule_type=RuleType.POLICY,
            priority=RulePriority.LOW,
            conditions=[
                RuleCondition("is_seasonal_product", "eq", True),
                RuleCondition("days_to_season_start", "lte", 60)
            ],
            actions=[
                # Analyze seasonal patterns
                RuleAction(
                    framework="langchain",
                    action="run_chain",
                    parameters={
                        "chain_name": "seasonal_analyzer",
                        "historical_seasons": 3,
                        "adjustment_factors": ["weather", "holidays", "trends"]
                    }
                ),
                # Adjust reorder parameters
                RuleAction(
                    framework="semantic_kernel",
                    action="run_skill",
                    parameters={
                        "skill_name": "InventoryPlanner",
                        "function_name": "AdjustSeasonalParameters"
                    }
                ),
                # Store seasonal insights
                RuleAction(
                    framework="zep",
                    action="extract_facts",
                    parameters={
                        "fact_type": "seasonal_pattern",
                        "confidence": 0.85
                    }
                )
            ],
            description="Adjust inventory levels for seasonal demand patterns"
        )
        self.rules.append(seasonal_adjustment_rule)
        
    async def manage_product_inventory(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage inventory for a specific product.
        
        Args:
            product: Product details including current inventory
            
        Returns:
            Management results and recommendations
        """
        # Prepare context
        context = {
            "product": product,
            "product_id": product.get("id"),
            "current_inventory": product.get("inventory_level", 0),
            "location_count": len(product.get("locations", [])),
            "is_seasonal_product": product.get("seasonal", False),
            "historical_data_months": await self._get_historical_data_months(product["id"]),
            "current_date": datetime.utcnow().isoformat(),
            "current_date_plus_90": (datetime.utcnow() + timedelta(days=90)).isoformat()
        }
        
        # Calculate additional metrics
        sales_metrics = await self._calculate_sales_metrics(product["id"])
        context.update(sales_metrics)
        
        # Start inventory management coordination
        await self.event_bus.publish(
            EventType.COORDINATION_STARTED,
            {
                "coordination_id": f"inventory_{product['id']}_{datetime.utcnow().timestamp()}",
                "frameworks": ["fastmcp", "temporal", "langchain", "zep", "mcp", "semantic_kernel"],
                "rule_ids": [rule.id for rule in self.rules]
            }
        )
        
        results = {}
        recommendations = []
        
        # Execute applicable rules
        for rule in self.rules:
            if rule.should_execute(context):
                logger.info(f"Executing inventory rule: {rule.name}")
                
                try:
                    rule_results = await self.orchestrator.execute_rule(rule, context)
                    results[rule.name] = rule_results
                    
                    # Update context with results
                    self._update_inventory_context(context, rule_results)
                    
                    # Extract recommendations
                    recommendations.extend(self._extract_recommendations(rule_results))
                    
                except Exception as e:
                    logger.error(f"Error executing rule {rule.name}: {e}")
                    results[rule.name] = {"error": str(e)}
                    
        # Generate inventory status
        inventory_status = self._generate_inventory_status(context, results)
        
        # Complete coordination
        await self.event_bus.publish(
            EventType.COORDINATION_COMPLETED,
            {
                "coordination_id": f"inventory_{product['id']}_{datetime.utcnow().timestamp()}",
                "frameworks": list(results.keys()),
                "results": inventory_status,
                "duration_ms": 0  # Would calculate actual
            }
        )
        
        return {
            "product_id": product["id"],
            "current_inventory": context["current_inventory"],
            "inventory_status": inventory_status,
            "rules_executed": len(results),
            "recommendations": recommendations,
            "next_reorder_date": context.get("next_reorder_date"),
            "predicted_stockout_date": context.get("predicted_stockout_date")
        }
        
    async def _get_historical_data_months(self, product_id: str) -> int:
        """Get the number of months of historical data available."""
        # Query Zep for oldest data point
        oldest_data = await self.orchestrator.execute_rule(
            BusinessRule(
                name="historical_data_query",
                actions=[
                    RuleAction(
                        framework="zep",
                        action="retrieve_memory",
                        parameters={
                            "session_id": f"product_{product_id}",
                            "limit": 1,
                            "types": ["sales", "inventory_level"]
                        }
                    )
                ]
            ),
            {}
        )
        
        # Calculate months
        memories = oldest_data.get("zep", {}).get("memories", [])
        if memories:
            oldest_timestamp = memories[0].get("timestamp")
            if oldest_timestamp:
                oldest_date = datetime.fromisoformat(oldest_timestamp)
                months = (datetime.utcnow() - oldest_date).days / 30
                return int(months)
                
        return 0
        
    async def _calculate_sales_metrics(self, product_id: str) -> Dict[str, Any]:
        """Calculate sales metrics for inventory planning."""
        # Get recent sales data
        recent_sales = await self.orchestrator.execute_rule(
            BusinessRule(
                name="sales_data_query",
                actions=[
                    RuleAction(
                        framework="zep",
                        action="retrieve_memory",
                        parameters={
                            "session_id": f"product_{product_id}",
                            "time_range": {
                                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                                "end": datetime.utcnow().isoformat()
                            },
                            "types": ["sales"]
                        }
                    )
                ]
            ),
            {}
        )
        
        # Calculate metrics
        sales_data = recent_sales.get("zep", {}).get("memories", [])
        daily_sales = [s.get("metadata", {}).get("quantity", 0) for s in sales_data]
        
        if daily_sales:
            daily_sales_avg = sum(daily_sales) / len(daily_sales)
            sales_volatility = self._calculate_volatility(daily_sales)
        else:
            daily_sales_avg = 0
            sales_volatility = 0
            
        return {
            "daily_sales_avg": daily_sales_avg,
            "sales_volatility": sales_volatility,
            "enable_predictive_analytics": len(daily_sales) > 30,
            "lead_time": 7,  # Default 7 days, would be from supplier data
            "allocation_needed": daily_sales_avg > 0
        }
        
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) of values."""
        if not values or len(values) < 2:
            return 0
            
        mean = sum(values) / len(values)
        if mean == 0:
            return 0
            
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        return std_dev / mean
        
    def _update_inventory_context(self, context: Dict[str, Any], results: Dict[str, Any]):
        """Update context based on rule execution results."""
        # Update reorder threshold from FastMCP calculation
        if "fastmcp" in results:
            fastmcp_result = results["fastmcp"]
            if "result" in fastmcp_result:
                result = fastmcp_result["result"]
                if isinstance(result, dict):
                    context["reorder_threshold"] = result.get("reorder_point", 0)
                    context["calculated_order_quantity"] = result.get("order_quantity", 0)
                    
        # Update demand predictions from LangChain
        if "langchain" in results:
            langchain_result = results["langchain"]
            if "result" in langchain_result:
                predictions = langchain_result["result"]
                if isinstance(predictions, dict):
                    context["predicted_demand_30d"] = predictions.get("demand_forecast", 0)
                    context["confidence_level"] = predictions.get("confidence", 0)
                    
        # Calculate dates
        if "daily_sales_avg" in context and context["daily_sales_avg"] > 0:
            days_of_stock = context["current_inventory"] / context["daily_sales_avg"]
            context["predicted_stockout_date"] = (
                datetime.utcnow() + timedelta(days=int(days_of_stock))
            ).isoformat()
            
            if "reorder_threshold" in context:
                days_to_reorder = (context["current_inventory"] - context["reorder_threshold"]) / context["daily_sales_avg"]
                if days_to_reorder > 0:
                    context["next_reorder_date"] = (
                        datetime.utcnow() + timedelta(days=int(days_to_reorder))
                    ).isoformat()
                    
    def _extract_recommendations(self, rule_results: Dict[str, Any]) -> List[str]:
        """Extract actionable recommendations from rule results."""
        recommendations = []
        
        # Check FastMCP results
        if "fastmcp" in rule_results:
            result = rule_results["fastmcp"].get("result", {})
            if result.get("safety_stock_low"):
                recommendations.append("Consider increasing safety stock due to high volatility")
                
        # Check LangChain predictions
        if "langchain" in rule_results:
            result = rule_results["langchain"].get("result", {})
            if result.get("trend") == "increasing":
                recommendations.append("Demand trend is increasing - consider larger reorder quantities")
            elif result.get("seasonality_detected"):
                recommendations.append("Seasonal pattern detected - adjust reorder points accordingly")
                
        # Check allocation results
        if "semantic_kernel" in rule_results:
            result = rule_results["semantic_kernel"].get("result", {})
            if result.get("imbalance_detected"):
                recommendations.append("Inventory imbalance detected across locations")
                
        return recommendations
        
    def _generate_inventory_status(self, context: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive inventory status."""
        current_inventory = context["current_inventory"]
        daily_sales_avg = context.get("daily_sales_avg", 0)
        reorder_threshold = context.get("reorder_threshold", 0)
        
        # Calculate status
        if current_inventory <= 0:
            status = "out_of_stock"
        elif current_inventory <= reorder_threshold:
            status = "reorder_required"
        elif daily_sales_avg > 0:
            days_of_stock = current_inventory / daily_sales_avg
            if days_of_stock < 7:
                status = "low_stock"
            elif days_of_stock > 90:
                status = "overstock"
            else:
                status = "optimal"
        else:
            status = "no_movement"
            
        return {
            "status": status,
            "current_level": current_inventory,
            "reorder_threshold": reorder_threshold,
            "days_of_stock": current_inventory / daily_sales_avg if daily_sales_avg > 0 else float('inf'),
            "predicted_demand_30d": context.get("predicted_demand_30d", 0),
            "confidence": context.get("confidence_level", 0)
        }
        
    async def optimize_multi_location_inventory(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize inventory across multiple locations."""
        # Aggregate inventory data
        total_inventory = sum(loc.get("inventory", 0) for loc in locations)
        total_capacity = sum(loc.get("capacity", 0) for loc in locations)
        
        # Create optimization context
        context = {
            "location_count": len(locations),
            "total_inventory": total_inventory,
            "total_capacity": total_capacity,
            "utilization": total_inventory / total_capacity if total_capacity > 0 else 0,
            "locations": locations,
            "allocation_needed": True
        }
        
        # Execute allocation rule
        allocation_result = await self.orchestrator.execute_rule(
            self.rules[3],  # Multi-location allocation rule
            context
        )
        
        # Generate transfer plan
        transfer_plan = self._generate_transfer_plan(locations, allocation_result)
        
        return {
            "optimization_status": "completed",
            "transfer_plan": transfer_plan,
            "expected_balance_improvement": self._calculate_balance_improvement(transfer_plan),
            "execution_steps": len(transfer_plan)
        }
        
    def _generate_transfer_plan(self, locations: List[Dict[str, Any]], allocation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate transfer plan based on allocation results."""
        transfer_plan = []
        
        # Extract allocation from results
        allocation = allocation_result.get("fastmcp", {}).get("result", {}).get("allocation", {})
        
        for location in locations:
            loc_id = location["id"]
            current = location.get("inventory", 0)
            target = allocation.get(loc_id, current)
            
            if target != current:
                transfer_plan.append({
                    "location_id": loc_id,
                    "current_inventory": current,
                    "target_inventory": target,
                    "transfer_quantity": target - current,
                    "priority": "high" if abs(target - current) > 100 else "normal"
                })
                
        return transfer_plan
        
    def _calculate_balance_improvement(self, transfer_plan: List[Dict[str, Any]]) -> float:
        """Calculate expected improvement in inventory balance."""
        if not transfer_plan:
            return 0.0
            
        # Calculate variance reduction
        current_variance = sum(t["current_inventory"] ** 2 for t in transfer_plan)
        target_variance = sum(t["target_inventory"] ** 2 for t in transfer_plan)
        
        if current_variance > 0:
            improvement = (current_variance - target_variance) / current_variance
            return max(0, min(1, improvement))
            
        return 0.0