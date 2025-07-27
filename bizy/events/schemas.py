"""
Event Schemas: Type-safe event definitions for cross-framework coordination.

This module defines Pydantic schemas for all events used in the orchestration system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Standard event types in the orchestration system."""
    # Rule execution events
    RULE_EXECUTION_STARTED = "rule_execution_started"
    RULE_EXECUTION_COMPLETED = "rule_execution_completed"
    RULE_EXECUTION_FAILED = "rule_execution_failed"
    
    # Framework events
    FRAMEWORK_CONNECTED = "framework_connected"
    FRAMEWORK_DISCONNECTED = "framework_disconnected"
    FRAMEWORK_ERROR = "framework_error"
    
    # Coordination events
    COORDINATION_STARTED = "coordination_started"
    COORDINATION_COMPLETED = "coordination_completed"
    COORDINATION_FAILED = "coordination_failed"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    HEALTH_CHECK = "health_check"


class BaseEventSchema(BaseModel):
    """Base schema for all events."""
    event_id: str = Field(description="Unique event identifier")
    event_type: EventType = Field(description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = Field(None, description="Source of the event")
    correlation_id: Optional[str] = Field(None, description="ID for correlating related events")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RuleExecutionStartedEvent(BaseEventSchema):
    """Event emitted when rule execution begins."""
    event_type: EventType = EventType.RULE_EXECUTION_STARTED
    rule_id: str = Field(description="ID of the rule being executed")
    rule_name: str = Field(description="Name of the rule")
    adapter: str = Field(description="Framework adapter executing the rule")
    context: Dict[str, Any] = Field(description="Execution context")


class RuleExecutionCompletedEvent(BaseEventSchema):
    """Event emitted when rule execution completes successfully."""
    event_type: EventType = EventType.RULE_EXECUTION_COMPLETED
    rule_id: str = Field(description="ID of the executed rule")
    rule_name: str = Field(description="Name of the rule")
    adapter: str = Field(description="Framework adapter that executed the rule")
    result: Dict[str, Any] = Field(description="Execution results")
    duration_ms: float = Field(description="Execution duration in milliseconds")


class RuleExecutionFailedEvent(BaseEventSchema):
    """Event emitted when rule execution fails."""
    event_type: EventType = EventType.RULE_EXECUTION_FAILED
    rule_id: str = Field(description="ID of the failed rule")
    rule_name: str = Field(description="Name of the rule")
    adapter: str = Field(description="Framework adapter where execution failed")
    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")


class FrameworkConnectedEvent(BaseEventSchema):
    """Event emitted when a framework adapter connects."""
    event_type: EventType = EventType.FRAMEWORK_CONNECTED
    framework: str = Field(description="Framework name")
    adapter: str = Field(description="Adapter name")
    capabilities: List[str] = Field(description="List of adapter capabilities")
    config: Dict[str, Any] = Field(description="Adapter configuration (non-sensitive)")


class FrameworkDisconnectedEvent(BaseEventSchema):
    """Event emitted when a framework adapter disconnects."""
    event_type: EventType = EventType.FRAMEWORK_DISCONNECTED
    framework: str = Field(description="Framework name")
    adapter: str = Field(description="Adapter name")
    reason: Optional[str] = Field(None, description="Disconnection reason")


class FrameworkErrorEvent(BaseEventSchema):
    """Event emitted when a framework encounters an error."""
    event_type: EventType = EventType.FRAMEWORK_ERROR
    framework: str = Field(description="Framework name")
    adapter: str = Field(description="Adapter name")
    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    recoverable: bool = Field(description="Whether the error is recoverable")


class CoordinationStartedEvent(BaseEventSchema):
    """Event emitted when multi-framework coordination begins."""
    event_type: EventType = EventType.COORDINATION_STARTED
    coordination_id: str = Field(description="Unique coordination identifier")
    frameworks: List[str] = Field(description="List of frameworks involved")
    rule_ids: List[str] = Field(description="List of rules being coordinated")


class CoordinationCompletedEvent(BaseEventSchema):
    """Event emitted when multi-framework coordination completes."""
    event_type: EventType = EventType.COORDINATION_COMPLETED
    coordination_id: str = Field(description="Unique coordination identifier")
    frameworks: List[str] = Field(description="List of frameworks involved")
    results: Dict[str, Any] = Field(description="Coordination results by framework")
    duration_ms: float = Field(description="Total coordination duration")


class CoordinationFailedEvent(BaseEventSchema):
    """Event emitted when multi-framework coordination fails."""
    event_type: EventType = EventType.COORDINATION_FAILED
    coordination_id: str = Field(description="Unique coordination identifier")
    frameworks: List[str] = Field(description="List of frameworks involved")
    failed_frameworks: List[str] = Field(description="Frameworks that failed")
    errors: Dict[str, str] = Field(description="Errors by framework")


class SystemStartupEvent(BaseEventSchema):
    """Event emitted when the orchestration system starts."""
    event_type: EventType = EventType.SYSTEM_STARTUP
    version: str = Field(description="System version")
    config: Dict[str, Any] = Field(description="System configuration")
    available_frameworks: List[str] = Field(description="Available framework adapters")


class SystemShutdownEvent(BaseEventSchema):
    """Event emitted when the orchestration system shuts down."""
    event_type: EventType = EventType.SYSTEM_SHUTDOWN
    reason: str = Field(description="Shutdown reason")
    graceful: bool = Field(description="Whether shutdown was graceful")


class HealthCheckEvent(BaseEventSchema):
    """Event emitted during health checks."""
    event_type: EventType = EventType.HEALTH_CHECK
    overall_status: str = Field(description="Overall system health status")
    framework_status: Dict[str, str] = Field(description="Health status by framework")
    metrics: Dict[str, Any] = Field(description="System metrics")


# Event factory for creating typed events
class EventFactory:
    """Factory for creating type-safe events."""
    
    @staticmethod
    def create_rule_execution_started(
        rule_id: str,
        rule_name: str,
        adapter: str,
        context: Dict[str, Any],
        source: Optional[str] = None
    ) -> RuleExecutionStartedEvent:
        """Create a rule execution started event."""
        return RuleExecutionStartedEvent(
            event_id=f"rule_start_{rule_id}_{datetime.utcnow().timestamp()}",
            rule_id=rule_id,
            rule_name=rule_name,
            adapter=adapter,
            context=context,
            source=source
        )
    
    @staticmethod
    def create_rule_execution_completed(
        rule_id: str,
        rule_name: str,
        adapter: str,
        result: Dict[str, Any],
        duration_ms: float,
        source: Optional[str] = None
    ) -> RuleExecutionCompletedEvent:
        """Create a rule execution completed event."""
        return RuleExecutionCompletedEvent(
            event_id=f"rule_complete_{rule_id}_{datetime.utcnow().timestamp()}",
            rule_id=rule_id,
            rule_name=rule_name,
            adapter=adapter,
            result=result,
            duration_ms=duration_ms,
            source=source
        )
    
    @staticmethod
    def create_rule_execution_failed(
        rule_id: str,
        rule_name: str,
        adapter: str,
        error: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        source: Optional[str] = None
    ) -> RuleExecutionFailedEvent:
        """Create a rule execution failed event."""
        return RuleExecutionFailedEvent(
            event_id=f"rule_failed_{rule_id}_{datetime.utcnow().timestamp()}",
            rule_id=rule_id,
            rule_name=rule_name,
            adapter=adapter,
            error=error,
            error_type=error_type,
            stack_trace=stack_trace,
            source=source
        )