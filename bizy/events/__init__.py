"""Event system for cross-framework coordination."""

from .event_bus import Event, EventBus, PersistentEventBus
from .schemas import (
    EventType,
    BaseEventSchema,
    RuleExecutionStartedEvent,
    RuleExecutionCompletedEvent,
    RuleExecutionFailedEvent,
    FrameworkConnectedEvent,
    FrameworkDisconnectedEvent,
    FrameworkErrorEvent,
    CoordinationStartedEvent,
    CoordinationCompletedEvent,
    CoordinationFailedEvent,
    SystemStartupEvent,
    SystemShutdownEvent,
    HealthCheckEvent,
    EventFactory
)
from .routing import EventRouter, EventRoute, RouteCondition, RouteConditionOperator, EventFilter
from .persistence import EventPersistenceManager, StorageBackend

__all__ = [
    # Event Bus
    "Event",
    "EventBus",
    "PersistentEventBus",
    
    # Schemas
    "EventType",
    "BaseEventSchema",
    "RuleExecutionStartedEvent",
    "RuleExecutionCompletedEvent",
    "RuleExecutionFailedEvent",
    "FrameworkConnectedEvent",
    "FrameworkDisconnectedEvent",
    "FrameworkErrorEvent",
    "CoordinationStartedEvent",
    "CoordinationCompletedEvent",
    "CoordinationFailedEvent",
    "SystemStartupEvent",
    "SystemShutdownEvent",
    "HealthCheckEvent",
    "EventFactory",
    
    # Routing
    "EventRouter",
    "EventRoute",
    "RouteCondition",
    "RouteConditionOperator",
    "EventFilter",
    
    # Persistence
    "EventPersistenceManager",
    "StorageBackend"
]
