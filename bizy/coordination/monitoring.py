"""
Monitoring: Observability and metrics for cross-framework coordination.

This module provides comprehensive monitoring capabilities for tracking
performance, errors, and coordination patterns.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import logging
import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import statistics

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Represents a single metric."""
    name: str
    type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


@dataclass
class MetricAggregation:
    """Aggregated metric statistics."""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    
    def add(self, value: float):
        """Add value to aggregation."""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        
    @property
    def average(self) -> float:
        """Calculate average."""
        return self.sum / self.count if self.count > 0 else 0.0


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.
    
    Features:
    - Multiple metric types
    - Time-window aggregation
    - Label-based filtering
    - Export capabilities
    """
    
    def __init__(self, window_size: int = 300):  # 5 minute default window
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.aggregations: Dict[str, MetricAggregation] = defaultdict(MetricAggregation)
        
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric."""
        metric = Metric(name, MetricType.COUNTER, value, labels=labels or {})
        self._add_metric(metric)
        
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric."""
        metric = Metric(name, MetricType.GAUGE, value, labels=labels or {})
        self._add_metric(metric)
        
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        metric = Metric(name, MetricType.HISTOGRAM, value, labels=labels or {})
        self._add_metric(metric)
        
    def _add_metric(self, metric: Metric):
        """Add metric to collection."""
        key = self._metric_key(metric.name, metric.labels)
        self.metrics[key].append(metric)
        self.aggregations[key].add(metric.value)
        
    def _metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate unique key for metric."""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}" if label_str else name
        
    def get_metrics(
        self,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Metric]:
        """Get metrics with optional filtering."""
        current_time = time.time()
        start_time = start_time or (current_time - self.window_size)
        end_time = end_time or current_time
        
        results = []
        
        for key, metric_list in self.metrics.items():
            # Filter by name if specified
            if name and not any(m.name == name for m in metric_list):
                continue
                
            # Filter by labels if specified
            if labels:
                matching_metrics = [
                    m for m in metric_list
                    if all(m.labels.get(k) == v for k, v in labels.items())
                ]
            else:
                matching_metrics = list(metric_list)
                
            # Filter by time range
            for metric in matching_metrics:
                if start_time <= metric.timestamp <= end_time:
                    results.append(metric)
                    
        return results
        
    def get_aggregation(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricAggregation]:
        """Get aggregated statistics for a metric."""
        key = self._metric_key(name, labels or {})
        return self.aggregations.get(key)
        
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for key, metrics in self.metrics.items():
            if metrics:
                latest = metrics[-1]
                metric_groups[latest.name].append((key, latest))
                
        # Generate Prometheus format
        for metric_name, entries in metric_groups.items():
            # Add HELP and TYPE lines
            lines.append(f"# HELP {metric_name} {metric_name}")
            if entries:
                lines.append(f"# TYPE {metric_name} {entries[0][1].type.value}")
                
            # Add metric lines
            for key, metric in entries:
                label_str = ",".join(
                    f'{k}="{v}"' for k, v in metric.labels.items()
                )
                if label_str:
                    lines.append(f"{metric_name}{{{label_str}}} {metric.value}")
                else:
                    lines.append(f"{metric_name} {metric.value}")
                    
        return "\n".join(lines)
        
    def clear_old_metrics(self, retention_seconds: float = 3600):
        """Clear metrics older than retention period."""
        cutoff_time = time.time() - retention_seconds
        
        for key in list(self.metrics.keys()):
            # Remove old metrics
            self.metrics[key] = deque(
                (m for m in self.metrics[key] if m.timestamp > cutoff_time),
                maxlen=10000
            )
            
            # Remove empty entries
            if not self.metrics[key]:
                del self.metrics[key]
                del self.aggregations[key]


class CoordinationMonitor:
    """
    Monitors cross-framework coordination patterns and performance.
    
    Features:
    - Execution tracking
    - Pattern detection
    - Performance analysis
    - Anomaly detection
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics = metrics_collector or MetricsCollector()
        self.execution_history: deque = deque(maxlen=1000)
        self.pattern_detectors: Dict[str, Callable] = {}
        self.anomaly_thresholds: Dict[str, float] = {}
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Initialize pattern detection."""
        # Register built-in pattern detectors
        self.pattern_detectors = {
            "cascade_failure": self._detect_cascade_failure,
            "performance_degradation": self._detect_performance_degradation,
            "framework_imbalance": self._detect_framework_imbalance,
            "error_spike": self._detect_error_spike
        }
        
        # Default anomaly thresholds
        self.anomaly_thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "response_time_multiplier": 3.0,  # 3x normal response time
            "framework_imbalance": 0.5  # 50% concentration
        }
        
    async def record_execution(
        self,
        rule_id: str,
        frameworks: List[str],
        start_time: float,
        end_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record a rule execution."""
        execution = {
            "rule_id": rule_id,
            "frameworks": frameworks,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "success": success,
            "error": error,
            "timestamp": time.time()
        }
        
        self.execution_history.append(execution)
        
        # Record metrics
        self.metrics.record_counter(
            "rule_executions_total",
            labels={"rule_id": rule_id, "status": "success" if success else "failure"}
        )
        
        self.metrics.record_histogram(
            "rule_execution_duration_seconds",
            execution["duration"],
            labels={"rule_id": rule_id}
        )
        
        for framework in frameworks:
            self.metrics.record_counter(
                "framework_executions_total",
                labels={"framework": framework}
            )
            
    def detect_patterns(self, window_seconds: float = 300) -> Dict[str, Any]:
        """Detect coordination patterns in recent executions."""
        patterns = {}
        current_time = time.time()
        
        # Filter recent executions
        recent_executions = [
            e for e in self.execution_history
            if current_time - e["timestamp"] <= window_seconds
        ]
        
        # Run pattern detectors
        for pattern_name, detector in self.pattern_detectors.items():
            result = detector(recent_executions)
            if result["detected"]:
                patterns[pattern_name] = result
                
        return patterns
        
    def _detect_cascade_failure(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect cascade failure pattern."""
        if len(executions) < 10:
            return {"detected": False}
            
        # Look for rapid succession of failures
        failure_times = [
            e["timestamp"] for e in executions
            if not e["success"]
        ]
        
        if len(failure_times) < 5:
            return {"detected": False}
            
        # Check if failures are clustered
        time_diffs = [
            failure_times[i+1] - failure_times[i]
            for i in range(len(failure_times)-1)
        ]
        
        avg_diff = statistics.mean(time_diffs) if time_diffs else float('inf')
        
        if avg_diff < 10:  # Failures within 10 seconds on average
            return {
                "detected": True,
                "failure_count": len(failure_times),
                "average_interval": avg_diff,
                "affected_rules": list(set(e["rule_id"] for e in executions if not e["success"]))
            }
            
        return {"detected": False}
        
    def _detect_performance_degradation(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect performance degradation pattern."""
        if len(executions) < 20:
            return {"detected": False}
            
        # Calculate average duration over time windows
        window_size = len(executions) // 4
        windows = []
        
        for i in range(0, len(executions) - window_size, window_size):
            window = executions[i:i+window_size]
            avg_duration = statistics.mean(e["duration"] for e in window)
            windows.append(avg_duration)
            
        if len(windows) < 2:
            return {"detected": False}
            
        # Check for increasing trend
        increasing = all(windows[i] < windows[i+1] for i in range(len(windows)-1))
        
        if increasing and windows[-1] > windows[0] * self.anomaly_thresholds["response_time_multiplier"]:
            return {
                "detected": True,
                "degradation_factor": windows[-1] / windows[0],
                "current_avg_duration": windows[-1],
                "baseline_avg_duration": windows[0]
            }
            
        return {"detected": False}
        
    def _detect_framework_imbalance(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect framework usage imbalance."""
        # Count framework usage
        framework_counts = defaultdict(int)
        total_frameworks = 0
        
        for execution in executions:
            for framework in execution["frameworks"]:
                framework_counts[framework] += 1
                total_frameworks += 1
                
        if total_frameworks == 0:
            return {"detected": False}
            
        # Calculate concentration
        max_usage = max(framework_counts.values()) if framework_counts else 0
        concentration = max_usage / total_frameworks
        
        if concentration > self.anomaly_thresholds["framework_imbalance"]:
            return {
                "detected": True,
                "dominant_framework": max(framework_counts, key=framework_counts.get),
                "concentration": concentration,
                "framework_distribution": dict(framework_counts)
            }
            
        return {"detected": False}
        
    def _detect_error_spike(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect error rate spike."""
        if len(executions) < 10:
            return {"detected": False}
            
        # Calculate error rate
        error_count = sum(1 for e in executions if not e["success"])
        error_rate = error_count / len(executions)
        
        if error_rate > self.anomaly_thresholds["error_rate"]:
            # Analyze error types
            error_types = defaultdict(int)
            for execution in executions:
                if not execution["success"] and execution.get("error"):
                    error_type = execution["error"].split(":")[0]
                    error_types[error_type] += 1
                    
            return {
                "detected": True,
                "error_rate": error_rate,
                "error_count": error_count,
                "total_executions": len(executions),
                "error_types": dict(error_types)
            }
            
        return {"detected": False}
        
    def get_performance_summary(self, window_seconds: float = 3600) -> Dict[str, Any]:
        """Get performance summary for the specified window."""
        current_time = time.time()
        
        # Filter recent executions
        recent_executions = [
            e for e in self.execution_history
            if current_time - e["timestamp"] <= window_seconds
        ]
        
        if not recent_executions:
            return {"message": "No executions in the specified window"}
            
        # Calculate statistics
        durations = [e["duration"] for e in recent_executions]
        success_count = sum(1 for e in recent_executions if e["success"])
        
        # Framework statistics
        framework_stats = defaultdict(lambda: {"count": 0, "total_duration": 0})
        for execution in recent_executions:
            for framework in execution["frameworks"]:
                framework_stats[framework]["count"] += 1
                framework_stats[framework]["total_duration"] += execution["duration"]
                
        # Calculate averages
        for stats in framework_stats.values():
            stats["average_duration"] = stats["total_duration"] / stats["count"]
            
        return {
            "window_seconds": window_seconds,
            "total_executions": len(recent_executions),
            "success_rate": success_count / len(recent_executions),
            "average_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "framework_statistics": dict(framework_stats),
            "detected_patterns": self.detect_patterns(window_seconds)
        }
        
    def export_traces(self, format: str = "jaeger") -> List[Dict[str, Any]]:
        """Export execution traces for distributed tracing."""
        traces = []
        
        for execution in self.execution_history:
            trace = {
                "traceID": f"trace_{execution['rule_id']}_{execution['start_time']}",
                "spans": []
            }
            
            # Create root span
            root_span = {
                "spanID": f"span_root_{execution['rule_id']}",
                "operationName": f"rule_execution_{execution['rule_id']}",
                "startTime": int(execution["start_time"] * 1000000),  # microseconds
                "duration": int(execution["duration"] * 1000000),
                "tags": [
                    {"key": "rule_id", "type": "string", "value": execution["rule_id"]},
                    {"key": "success", "type": "bool", "value": execution["success"]}
                ]
            }
            
            trace["spans"].append(root_span)
            
            # Create child spans for each framework
            for i, framework in enumerate(execution["frameworks"]):
                child_span = {
                    "spanID": f"span_{framework}_{i}",
                    "parentSpanID": root_span["spanID"],
                    "operationName": f"framework_execution_{framework}",
                    "startTime": int(execution["start_time"] * 1000000),
                    "duration": int(execution["duration"] / len(execution["frameworks"]) * 1000000),
                    "tags": [
                        {"key": "framework", "type": "string", "value": framework}
                    ]
                }
                trace["spans"].append(child_span)
                
            traces.append(trace)
            
        return traces


from typing import Callable