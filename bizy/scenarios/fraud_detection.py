"""
Fraud Detection Scenario.

Demonstrates real-time fraud detection using multiple frameworks for
transaction analysis, pattern recognition, and response coordination.
"""

from typing import Any, Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import statistics

from ..core.business_rule import (
    BusinessRule, RuleType, RulePriority, RuleCondition, RuleAction
)
from ..core.meta_orchestrator import MetaOrchestrator
from ..events import EventBus, EventType

logger = logging.getLogger(__name__)


class FraudDetectionScenario:
    """
    Implements a sophisticated fraud detection system that coordinates:
    - FastMCP for high-performance transaction analysis
    - LangChain for pattern recognition and anomaly detection
    - Temporal for case management workflows
    - Zep for historical pattern storage
    - MCP for external API integration
    - Semantic Kernel for fraud analyst communication
    """
    
    def __init__(self, orchestrator: MetaOrchestrator, event_bus: EventBus):
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.rules: List[BusinessRule] = []
        self._create_fraud_detection_rules()
        
    def _create_fraud_detection_rules(self):
        """Create business rules for fraud detection."""
        
        # Rule 1: Real-time Transaction Screening
        transaction_screening = BusinessRule(
            name="real_time_transaction_screening",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.CRITICAL,
            conditions=[
                RuleCondition("transaction_type", "in", ["payment", "transfer", "withdrawal"]),
                RuleCondition("amount", "gt", 0)
            ],
            actions=[
                # Fast initial screening with FastMCP
                RuleAction(
                    framework="fastmcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "velocity_checker",
                        "use_cache": False,  # Don't cache for real-time
                        "parameters": {
                            "check_types": ["frequency", "amount", "location"]
                        }
                    }
                ),
                # Store transaction for pattern analysis
                RuleAction(
                    framework="zep",
                    action="store_memory",
                    parameters={
                        "type": "transaction",
                        "metadata": {
                            "timestamp": "${transaction_timestamp}",
                            "amount": "${amount}",
                            "merchant": "${merchant}",
                            "location": "${location}"
                        }
                    }
                )
            ],
            description="Screen all transactions in real-time"
        )
        self.rules.append(transaction_screening)
        
        # Rule 2: High-Risk Transaction Analysis
        high_risk_analysis = BusinessRule(
            name="high_risk_transaction_analysis",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition("risk_score", "gt", 0.7),
                RuleCondition("amount", "gt", 1000)
            ],
            actions=[
                # Deep analysis with LangChain
                RuleAction(
                    framework="langchain",
                    action="run_agent",
                    parameters={
                        "agent_name": "fraud_analyst_agent",
                        "task": "Analyze transaction for fraud indicators",
                        "tools": ["pattern_matcher", "anomaly_detector", "risk_calculator"]
                    }
                ),
                # Start investigation workflow
                RuleAction(
                    framework="temporal",
                    action="start_workflow",
                    parameters={
                        "workflow_name": "fraud_investigation",
                        "workflow_id": "fraud_${transaction_id}",
                        "parameters": {
                            "priority": "high",
                            "auto_block": True
                        }
                    }
                ),
                # Check against known patterns
                RuleAction(
                    framework="zep",
                    action="semantic_search",
                    parameters={
                        "query": "similar fraud patterns",
                        "scope": ["facts"],
                        "limit": 10
                    }
                )
            ],
            description="Perform deep analysis on high-risk transactions"
        )
        self.rules.append(high_risk_analysis)
        
        # Rule 3: Velocity Check Rules
        velocity_check = BusinessRule(
            name="transaction_velocity_check",
            rule_type=RuleType.POLICY,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition("transaction_count_10min", "gt", 5),
                RuleCondition("distinct_locations_2hr", "gt", 2)
            ],
            actions=[
                # Block transaction immediately
                RuleAction(
                    framework="mcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "transaction_blocker",
                        "parameters": {
                            "action": "block",
                            "reason": "velocity_violation"
                        }
                    }
                ),
                # Notify fraud team
                RuleAction(
                    framework="semantic_kernel",
                    action="communicate_agent",
                    parameters={
                        "agent_id": "fraud_team",
                        "message_type": "alert",
                        "priority": "critical",
                        "message": "Velocity violation detected"
                    }
                )
            ],
            description="Check for rapid transaction velocity"
        )
        self.rules.append(velocity_check)
        
        # Rule 4: Machine Learning Pattern Detection
        ml_pattern_detection = BusinessRule(
            name="ml_pattern_detection",
            rule_type=RuleType.ACTION,
            priority=RulePriority.MEDIUM,
            conditions=[
                RuleCondition("enable_ml_analysis", "eq", True),
                RuleCondition("transaction_history_available", "eq", True)
            ],
            actions=[
                # Batch process with FastMCP
                RuleAction(
                    framework="fastmcp",
                    action="batch_execute",
                    parameters={
                        "executions": [
                            {
                                "tool_name": "feature_extractor",
                                "parameters": {"features": ["behavioral", "temporal", "network"]}
                            },
                            {
                                "tool_name": "ml_scorer",
                                "parameters": {"model": "fraud_detection_v2"}
                            }
                        ],
                        "parallel": True
                    }
                ),
                # Store patterns for future reference
                RuleAction(
                    framework="zep",
                    action="extract_facts",
                    parameters={
                        "fact_type": "fraud_pattern",
                        "confidence": "${ml_confidence}",
                        "source": "ml_analysis"
                    }
                )
            ],
            description="Apply machine learning for pattern detection"
        )
        self.rules.append(ml_pattern_detection)
        
        # Rule 5: Cross-Reference External Databases
        external_check = BusinessRule(
            name="external_database_check",
            rule_type=RuleType.ACTION,
            priority=RulePriority.MEDIUM,
            conditions=[
                RuleCondition("check_external_sources", "eq", True),
                RuleCondition("merchant_category", "in", ["high_risk", "international", "crypto"])
            ],
            actions=[
                # Query external APIs
                RuleAction(
                    framework="mcp",
                    action="execute_tool",
                    parameters={
                        "tool_name": "external_api_checker",
                        "parameters": {
                            "apis": ["merchant_verification", "sanctions_list", "fraud_database"],
                            "timeout": 5000
                        }
                    }
                ),
                # Process results with Semantic Kernel
                RuleAction(
                    framework="semantic_kernel",
                    action="run_skill",
                    parameters={
                        "skill_name": "DataAggregator",
                        "function_name": "MergeExternalResults"
                    }
                )
            ],
            description="Cross-reference with external fraud databases"
        )
        self.rules.append(external_check)
        
    async def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single transaction for fraud indicators.
        
        Args:
            transaction: Transaction details
            
        Returns:
            Analysis results including risk score and recommendations
        """
        # Prepare context with transaction data
        context = {
            "transaction_type": transaction.get("type", "payment"),
            "amount": transaction.get("amount", 0),
            "transaction_id": transaction.get("id", "unknown"),
            "transaction_timestamp": transaction.get("timestamp", datetime.utcnow().isoformat()),
            "merchant": transaction.get("merchant", {}),
            "location": transaction.get("location", {}),
            "customer_id": transaction.get("customer_id"),
            "device_info": transaction.get("device_info", {})
        }
        
        # Add velocity metrics
        velocity_metrics = await self._calculate_velocity_metrics(context["customer_id"])
        context.update(velocity_metrics)
        
        # Start analysis coordination
        await self.event_bus.publish(
            EventType.COORDINATION_STARTED,
            {
                "coordination_id": f"fraud_analysis_{context['transaction_id']}",
                "frameworks": ["fastmcp", "langchain", "temporal", "zep", "mcp", "semantic_kernel"],
                "rule_ids": [rule.id for rule in self.rules]
            }
        )
        
        results = {}
        risk_factors = []
        
        # Execute applicable rules
        for rule in self.rules:
            if rule.should_execute(context):
                logger.info(f"Executing fraud rule: {rule.name}")
                
                try:
                    rule_results = await self.orchestrator.execute_rule(rule, context)
                    results[rule.name] = rule_results
                    
                    # Extract risk factors
                    risk_factors.extend(self._extract_risk_factors(rule_results))
                    
                    # Update context with results
                    self._update_fraud_context(context, rule_results)
                    
                except Exception as e:
                    logger.error(f"Error executing rule {rule.name}: {e}")
                    results[rule.name] = {"error": str(e)}
                    
        # Calculate final risk score
        final_risk_score = self._calculate_final_risk_score(risk_factors)
        
        # Determine action
        action = self._determine_action(final_risk_score, risk_factors)
        
        # Complete coordination
        await self.event_bus.publish(
            EventType.COORDINATION_COMPLETED,
            {
                "coordination_id": f"fraud_analysis_{context['transaction_id']}",
                "frameworks": list(results.keys()),
                "results": {
                    "risk_score": final_risk_score,
                    "action": action
                },
                "duration_ms": 0  # Would calculate actual duration
            }
        )
        
        return {
            "transaction_id": context["transaction_id"],
            "risk_score": final_risk_score,
            "risk_factors": risk_factors,
            "action": action,
            "rules_executed": len(results),
            "analysis_details": results
        }
        
    async def _calculate_velocity_metrics(self, customer_id: str) -> Dict[str, Any]:
        """Calculate transaction velocity metrics for a customer."""
        # Query recent transactions from Zep
        recent_transactions = await self.orchestrator.execute_rule(
            BusinessRule(
                name="velocity_query",
                actions=[
                    RuleAction(
                        framework="zep",
                        action="retrieve_memory",
                        parameters={
                            "session_id": f"customer_{customer_id}",
                            "time_range": {
                                "start": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                                "end": datetime.utcnow().isoformat()
                            },
                            "types": ["transaction"]
                        }
                    )
                ]
            ),
            {}
        )
        
        # Calculate metrics
        transactions = recent_transactions.get("zep", {}).get("memories", [])
        
        # Transaction count in last 10 minutes
        ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
        recent_count = sum(1 for t in transactions 
                          if datetime.fromisoformat(t.get("timestamp", "")) > ten_min_ago)
        
        # Distinct locations in last 2 hours
        locations = set()
        for t in transactions:
            loc = t.get("metadata", {}).get("location", {})
            if loc:
                locations.add(f"{loc.get('country', '')}-{loc.get('city', '')}")
                
        return {
            "transaction_count_10min": recent_count,
            "distinct_locations_2hr": len(locations),
            "transaction_history_available": len(transactions) > 0
        }
        
    def _extract_risk_factors(self, rule_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract risk factors from rule execution results."""
        risk_factors = []
        
        # Extract from FastMCP velocity check
        if "fastmcp" in rule_results:
            velocity_result = rule_results["fastmcp"].get("result", {})
            if velocity_result.get("velocity_exceeded"):
                risk_factors.append({
                    "type": "velocity",
                    "severity": "high",
                    "details": velocity_result.get("details", "")
                })
                
        # Extract from LangChain analysis
        if "langchain" in rule_results:
            analysis = rule_results["langchain"].get("result", {})
            if analysis.get("anomalies"):
                for anomaly in analysis["anomalies"]:
                    risk_factors.append({
                        "type": "anomaly",
                        "severity": anomaly.get("severity", "medium"),
                        "details": anomaly.get("description", "")
                    })
                    
        # Extract from external checks
        if "mcp" in rule_results:
            external_results = rule_results["mcp"].get("result", {})
            if external_results.get("sanctions_hit"):
                risk_factors.append({
                    "type": "sanctions",
                    "severity": "critical",
                    "details": "Customer or merchant on sanctions list"
                })
                
        return risk_factors
        
    def _update_fraud_context(self, context: Dict[str, Any], results: Dict[str, Any]):
        """Update context based on rule execution results."""
        # Update risk score
        if "fastmcp" in results:
            fastmcp_result = results["fastmcp"]
            if "result" in fastmcp_result and "risk_score" in fastmcp_result["result"]:
                context["risk_score"] = fastmcp_result["result"]["risk_score"]
                
        # Update ML analysis availability
        context["enable_ml_analysis"] = context.get("transaction_history_available", False)
        
        # Update external check requirement
        merchant_category = context.get("merchant", {}).get("category", "")
        context["merchant_category"] = merchant_category
        context["check_external_sources"] = merchant_category in ["high_risk", "international", "crypto"]
        
    def _calculate_final_risk_score(self, risk_factors: List[Dict[str, Any]]) -> float:
        """Calculate final risk score based on all risk factors."""
        if not risk_factors:
            return 0.0
            
        # Weight factors by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2
        }
        
        # Calculate weighted score
        total_weight = 0
        weighted_sum = 0
        
        for factor in risk_factors:
            severity = factor.get("severity", "medium")
            weight = severity_weights.get(severity, 0.4)
            total_weight += weight
            weighted_sum += weight
            
        # Normalize to 0-1 range
        if total_weight > 0:
            risk_score = min(weighted_sum / total_weight, 1.0)
        else:
            risk_score = 0.0
            
        return risk_score
        
    def _determine_action(self, risk_score: float, risk_factors: List[Dict[str, Any]]) -> str:
        """Determine action based on risk score and factors."""
        # Check for critical factors
        has_critical = any(f.get("severity") == "critical" for f in risk_factors)
        
        if has_critical or risk_score > 0.9:
            return "block"
        elif risk_score > 0.7:
            return "review"
        elif risk_score > 0.5:
            return "flag"
        else:
            return "approve"
            
    async def generate_fraud_report(self, time_period: Dict[str, str]) -> Dict[str, Any]:
        """Generate comprehensive fraud analysis report."""
        # Query historical fraud data
        fraud_data = await self.orchestrator.execute_rule(
            BusinessRule(
                name="fraud_data_query",
                actions=[
                    RuleAction(
                        framework="zep",
                        action="query_knowledge",
                        parameters={
                            "query_type": "nodes",
                            "entity": "fraud_pattern",
                            "time_range": time_period
                        }
                    )
                ]
            ),
            {}
        )
        
        # Analyze patterns with LangChain
        pattern_analysis = await self.orchestrator.execute_rule(
            BusinessRule(
                name="pattern_analysis",
                actions=[
                    RuleAction(
                        framework="langchain",
                        action="run_chain",
                        parameters={
                            "chain_name": "fraud_pattern_analyzer",
                            "data": fraud_data,
                            "analysis_type": "trend_detection"
                        }
                    )
                ]
            ),
            {}
        )
        
        return {
            "time_period": time_period,
            "total_transactions_analyzed": fraud_data.get("count", 0),
            "fraud_patterns_detected": pattern_analysis.get("patterns", []),
            "recommendations": self._generate_fraud_recommendations(pattern_analysis),
            "risk_trend": pattern_analysis.get("trend", "stable")
        }
        
    def _generate_fraud_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on fraud pattern analysis."""
        recommendations = []
        
        patterns = analysis.get("patterns", [])
        
        # Analyze patterns for recommendations
        if any(p.get("type") == "velocity" for p in patterns):
            recommendations.append("Consider implementing stricter velocity controls")
            
        if any(p.get("type") == "geographic" for p in patterns):
            recommendations.append("Enhanced geographic risk scoring recommended")
            
        if len(patterns) > 10:
            recommendations.append("High pattern diversity suggests evolving fraud tactics")
            
        return recommendations