"""
Event Routing: Advanced routing and filtering for cross-framework events.

This module provides sophisticated event routing capabilities including
filtering, transformation, and conditional routing.
"""

from typing import Any, Callable, Dict, List, Optional, Set
import re
import logging
from dataclasses import dataclass
from enum import Enum

from .event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class RouteConditionOperator(Enum):
    """Operators for route conditions."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    CONTAINS = "contains"
    MATCHES = "matches"  # Regex match
    IN = "in"
    NOT_IN = "not_in"


@dataclass
class RouteCondition:
    """Condition for event routing."""
    field: str  # Dot-notation path to field in event data
    operator: RouteConditionOperator
    value: Any
    
    def evaluate(self, event: Event) -> bool:
        """Evaluate if the event matches this condition."""
        field_value = self._get_field_value(event)
        
        if field_value is None:
            return False
            
        try:
            if self.operator == RouteConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == RouteConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == RouteConditionOperator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == RouteConditionOperator.LESS_THAN:
                return field_value < self.value
            elif self.operator == RouteConditionOperator.CONTAINS:
                return self.value in str(field_value)
            elif self.operator == RouteConditionOperator.MATCHES:
                return re.match(self.value, str(field_value)) is not None
            elif self.operator == RouteConditionOperator.IN:
                return field_value in self.value
            elif self.operator == RouteConditionOperator.NOT_IN:
                return field_value not in self.value
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
            
    def _get_field_value(self, event: Event) -> Any:
        """Extract field value from event using dot notation."""
        parts = self.field.split('.')
        
        # Start with event attributes
        if parts[0] == 'event_type':
            value = event.event_type
        elif parts[0] == 'source':
            value = event.source
        elif parts[0] == 'data':
            value = event.data
            parts = parts[1:]  # Remove 'data' prefix
        else:
            # Try to get from event data directly
            value = event.data
            
        # Navigate through nested fields
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
                
        return value


@dataclass
class EventRoute:
    """Defines a routing rule for events."""
    name: str
    conditions: List[RouteCondition]
    handler: Callable[[Event], None]
    transform: Optional[Callable[[Event], Event]] = None
    enabled: bool = True
    
    def matches(self, event: Event) -> bool:
        """Check if the event matches all conditions."""
        if not self.enabled:
            return False
            
        # All conditions must match
        return all(condition.evaluate(event) for condition in self.conditions)
        
    async def handle(self, event: Event) -> None:
        """Handle the event, applying transformation if configured."""
        try:
            # Apply transformation if configured
            if self.transform:
                event = self.transform(event)
                
            # Call handler
            if asyncio.iscoroutinefunction(self.handler):
                await self.handler(event)
            else:
                self.handler(event)
        except Exception as e:
            logger.error(f"Error in route handler {self.name}: {e}")


class EventRouter:
    """
    Advanced event router with filtering and transformation capabilities.
    
    Provides sophisticated routing of events based on conditions,
    with support for transformation and multiple handlers per event.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.routes: Dict[str, EventRoute] = {}
        self.event_type_routes: Dict[str, Set[str]] = {}  # Index for performance
        
        # Subscribe to all events
        self.event_bus.subscribe("*", self._handle_event)
        
    def add_route(self, route: EventRoute) -> None:
        """Add a routing rule."""
        self.routes[route.name] = route
        
        # Index by event type for performance
        for condition in route.conditions:
            if condition.field == "event_type" and condition.operator == RouteConditionOperator.EQUALS:
                event_type = condition.value
                if event_type not in self.event_type_routes:
                    self.event_type_routes[event_type] = set()
                self.event_type_routes[event_type].add(route.name)
                
        logger.info(f"Added route: {route.name}")
        
    def remove_route(self, name: str) -> None:
        """Remove a routing rule."""
        if name in self.routes:
            route = self.routes[name]
            del self.routes[name]
            
            # Update index
            for event_type, route_names in self.event_type_routes.items():
                route_names.discard(name)
                
            logger.info(f"Removed route: {name}")
            
    def enable_route(self, name: str) -> None:
        """Enable a routing rule."""
        if name in self.routes:
            self.routes[name].enabled = True
            
    def disable_route(self, name: str) -> None:
        """Disable a routing rule."""
        if name in self.routes:
            self.routes[name].enabled = False
            
    async def _handle_event(self, event: Event) -> None:
        """Handle incoming events and route them appropriately."""
        # Get potential routes based on event type
        potential_routes = set()
        
        # Add routes indexed by event type
        if event.event_type in self.event_type_routes:
            potential_routes.update(self.event_type_routes[event.event_type])
            
        # Add routes without event type conditions (catch-all routes)
        for name, route in self.routes.items():
            has_event_type_condition = any(
                c.field == "event_type" for c in route.conditions
            )
            if not has_event_type_condition:
                potential_routes.add(name)
                
        # Evaluate and execute matching routes
        tasks = []
        for route_name in potential_routes:
            route = self.routes.get(route_name)
            if route and route.matches(event):
                task = asyncio.create_task(route.handle(event))
                tasks.append(task)
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class EventFilter:
    """Utility class for creating common event filters."""
    
    @staticmethod
    def by_event_type(event_type: str) -> RouteCondition:
        """Filter by event type."""
        return RouteCondition(
            field="event_type",
            operator=RouteConditionOperator.EQUALS,
            value=event_type
        )
        
    @staticmethod
    def by_source(source: str) -> RouteCondition:
        """Filter by event source."""
        return RouteCondition(
            field="source",
            operator=RouteConditionOperator.EQUALS,
            value=source
        )
        
    @staticmethod
    def by_framework(framework: str) -> RouteCondition:
        """Filter by framework name in event data."""
        return RouteCondition(
            field="data.framework",
            operator=RouteConditionOperator.EQUALS,
            value=framework
        )
        
    @staticmethod
    def by_rule_id(rule_id: str) -> RouteCondition:
        """Filter by rule ID in event data."""
        return RouteCondition(
            field="data.rule_id",
            operator=RouteConditionOperator.EQUALS,
            value=rule_id
        )
        
    @staticmethod
    def by_error_pattern(pattern: str) -> RouteCondition:
        """Filter by error message pattern."""
        return RouteCondition(
            field="data.error",
            operator=RouteConditionOperator.MATCHES,
            value=pattern
        )


import asyncio