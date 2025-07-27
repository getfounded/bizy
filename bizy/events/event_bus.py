"""
Event Bus: Cross-framework event coordination system.

This module provides an async event bus for coordinating communication
between different framework adapters.
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Event:
    """Represents an event in the system."""
    
    def __init__(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None):
        self.id = f"{event_type}_{datetime.utcnow().timestamp()}"
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }


class EventBus:
    """
    Async event bus for cross-framework coordination.
    
    Provides publish/subscribe functionality for event-driven communication
    between framework adapters and the meta-orchestrator.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        
    async def publish(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event being published
            data: Event data
            source: Optional source identifier
        """
        event = Event(event_type, data, source)
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
            
        # Notify subscribers
        if event_type in self.subscribers:
            tasks = []
            for callback in self.subscribers[event_type]:
                task = asyncio.create_task(self._invoke_callback(callback, event))
                tasks.append(task)
                
            await asyncio.gather(*tasks, return_exceptions=True)
            
        logger.debug(f"Published event: {event_type} from {source}")
        
    async def _invoke_callback(self, callback: Callable, event: Event) -> None:
        """Invoke a subscriber callback with error handling."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")
            
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of events to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)
            if not self.subscribers[event_type]:
                del self.subscribers[event_type]
                
        logger.debug(f"Unsubscribed from event: {event_type}")
        
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of events matching criteria
        """
        history = self.event_history
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
            
        return history[-limit:]
        
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        logger.info("Event history cleared")


class PersistentEventBus(EventBus):
    """
    Event bus with persistence capabilities for event replay and debugging.
    
    Extends the base EventBus with the ability to persist events to storage
    and replay them for debugging or recovery purposes.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        super().__init__()
        self.storage_path = storage_path or "events.jsonl"
        
    async def publish(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
        """Publish event and persist to storage."""
        await super().publish(event_type, data, source)
        
        # Persist event
        event = self.event_history[-1]
        await self._persist_event(event)
        
    async def _persist_event(self, event: Event) -> None:
        """Persist event to storage."""
        try:
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist event: {e}")
            
    async def replay_events(self, start_time: Optional[datetime] = None) -> int:
        """
        Replay events from persistent storage.
        
        Args:
            start_time: Optional start time for replay
            
        Returns:
            Number of events replayed
        """
        replayed_count = 0
        
        try:
            with open(self.storage_path, 'r') as f:
                for line in f:
                    event_data = json.loads(line)
                    event_time = datetime.fromisoformat(event_data['timestamp'])
                    
                    if start_time and event_time < start_time:
                        continue
                        
                    # Republish event
                    await self.publish(
                        event_data['event_type'],
                        event_data['data'],
                        event_data['source']
                    )
                    replayed_count += 1
                    
        except FileNotFoundError:
            logger.warning(f"No event file found at {self.storage_path}")
        except Exception as e:
            logger.error(f"Error replaying events: {e}")
            
        return replayed_count