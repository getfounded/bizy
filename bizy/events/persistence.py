"""
Event Persistence: Storage and replay capabilities for events.

This module provides persistence mechanisms for events, enabling
debugging, audit trails, and event replay functionality.
"""

from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime, timedelta
import json
import asyncio
import aiofiles
import logging
from pathlib import Path
from enum import Enum

from .event_bus import Event

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """Supported storage backends for event persistence."""
    FILE = "file"
    REDIS = "redis"
    DATABASE = "database"


class EventPersistenceManager:
    """
    Manages event persistence across different storage backends.
    
    Provides capabilities for storing, retrieving, and replaying events
    for debugging and recovery purposes.
    """
    
    def __init__(self, backend: StorageBackend = StorageBackend.FILE, config: Dict[str, Any] = None):
        self.backend = backend
        self.config = config or {}
        self._initialize_backend()
        
    def _initialize_backend(self) -> None:
        """Initialize the storage backend."""
        if self.backend == StorageBackend.FILE:
            self.storage_path = Path(self.config.get('path', 'events'))
            self.storage_path.mkdir(exist_ok=True)
        elif self.backend == StorageBackend.REDIS:
            # Redis initialization would go here
            pass
        elif self.backend == StorageBackend.DATABASE:
            # Database initialization would go here
            pass
            
    async def persist_event(self, event: Event) -> None:
        """
        Persist an event to storage.
        
        Args:
            event: Event to persist
        """
        if self.backend == StorageBackend.FILE:
            await self._persist_to_file(event)
        elif self.backend == StorageBackend.REDIS:
            await self._persist_to_redis(event)
        elif self.backend == StorageBackend.DATABASE:
            await self._persist_to_database(event)
            
    async def _persist_to_file(self, event: Event) -> None:
        """Persist event to file storage."""
        try:
            # Create daily event files
            date_str = event.timestamp.strftime("%Y-%m-%d")
            file_path = self.storage_path / f"events_{date_str}.jsonl"
            
            async with aiofiles.open(file_path, 'a') as f:
                await f.write(json.dumps(event.to_dict()) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to persist event to file: {e}")
            
    async def _persist_to_redis(self, event: Event) -> None:
        """Persist event to Redis."""
        # Redis implementation would go here
        pass
        
    async def _persist_to_database(self, event: Event) -> None:
        """Persist event to database."""
        # Database implementation would go here
        pass
        
    async def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        source_filter: Optional[str] = None,
        limit: int = 1000
    ) -> List[Event]:
        """
        Retrieve events from storage with filtering.
        
        Args:
            start_time: Start time for event retrieval
            end_time: End time for event retrieval
            event_types: Filter by event types
            source_filter: Filter by event source
            limit: Maximum number of events to retrieve
            
        Returns:
            List of events matching criteria
        """
        if self.backend == StorageBackend.FILE:
            return await self._get_events_from_file(
                start_time, end_time, event_types, source_filter, limit
            )
        elif self.backend == StorageBackend.REDIS:
            return await self._get_events_from_redis(
                start_time, end_time, event_types, source_filter, limit
            )
        elif self.backend == StorageBackend.DATABASE:
            return await self._get_events_from_database(
                start_time, end_time, event_types, source_filter, limit
            )
            
    async def _get_events_from_file(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_types: Optional[List[str]],
        source_filter: Optional[str],
        limit: int
    ) -> List[Event]:
        """Retrieve events from file storage."""
        events = []
        
        # Determine which files to read
        if start_time and end_time:
            current_date = start_time.date()
            end_date = end_time.date()
            
            while current_date <= end_date:
                file_path = self.storage_path / f"events_{current_date}.jsonl"
                if file_path.exists():
                    events.extend(await self._read_events_from_file(
                        file_path, start_time, end_time, event_types, source_filter
                    ))
                current_date += timedelta(days=1)
        else:
            # Read all event files
            for file_path in sorted(self.storage_path.glob("events_*.jsonl")):
                events.extend(await self._read_events_from_file(
                    file_path, start_time, end_time, event_types, source_filter
                ))
                
        # Apply limit
        return events[:limit]
        
    async def _read_events_from_file(
        self,
        file_path: Path,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_types: Optional[List[str]],
        source_filter: Optional[str]
    ) -> List[Event]:
        """Read and filter events from a single file."""
        events = []
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                async for line in f:
                    event_data = json.loads(line)
                    
                    # Apply filters
                    event_time = datetime.fromisoformat(event_data['timestamp'])
                    
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue
                    if event_types and event_data['event_type'] not in event_types:
                        continue
                    if source_filter and event_data.get('source') != source_filter:
                        continue
                        
                    # Reconstruct event
                    event = Event(
                        event_type=event_data['event_type'],
                        data=event_data['data'],
                        source=event_data.get('source')
                    )
                    event.id = event_data['id']
                    event.timestamp = event_time
                    
                    events.append(event)
                    
        except Exception as e:
            logger.error(f"Error reading events from {file_path}: {e}")
            
        return events
        
    async def _get_events_from_redis(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_types: Optional[List[str]],
        source_filter: Optional[str],
        limit: int
    ) -> List[Event]:
        """Retrieve events from Redis."""
        # Redis implementation would go here
        return []
        
    async def _get_events_from_database(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_types: Optional[List[str]],
        source_filter: Optional[str],
        limit: int
    ) -> List[Event]:
        """Retrieve events from database."""
        # Database implementation would go here
        return []
        
    async def replay_events(
        self,
        event_bus,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        replay_speed: float = 1.0
    ) -> int:
        """
        Replay events through the event bus.
        
        Args:
            event_bus: Event bus to replay events through
            start_time: Start time for replay
            end_time: End time for replay
            event_types: Types of events to replay
            replay_speed: Speed multiplier for replay (1.0 = real-time)
            
        Returns:
            Number of events replayed
        """
        events = await self.get_events(start_time, end_time, event_types)
        
        if not events:
            return 0
            
        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        replayed = 0
        last_timestamp = None
        
        for event in events:
            # Calculate delay for realistic replay timing
            if last_timestamp and replay_speed > 0:
                time_diff = (event.timestamp - last_timestamp).total_seconds()
                delay = time_diff / replay_speed
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            # Replay event
            await event_bus.publish(
                event.event_type,
                event.data,
                event.source
            )
            
            replayed += 1
            last_timestamp = event.timestamp
            
        return replayed
        
    async def cleanup_old_events(self, retention_days: int = 30) -> int:
        """
        Clean up events older than retention period.
        
        Args:
            retention_days: Number of days to retain events
            
        Returns:
            Number of events cleaned up
        """
        if self.backend == StorageBackend.FILE:
            return await self._cleanup_file_events(retention_days)
        elif self.backend == StorageBackend.REDIS:
            return await self._cleanup_redis_events(retention_days)
        elif self.backend == StorageBackend.DATABASE:
            return await self._cleanup_database_events(retention_days)
            
    async def _cleanup_file_events(self, retention_days: int) -> int:
        """Clean up old event files."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        cleaned = 0
        
        for file_path in self.storage_path.glob("events_*.jsonl"):
            # Extract date from filename
            date_str = file_path.stem.replace("events_", "")
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff_date:
                    file_path.unlink()
                    cleaned += 1
                    logger.info(f"Deleted old event file: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                
        return cleaned
        
    async def _cleanup_redis_events(self, retention_days: int) -> int:
        """Clean up old events from Redis."""
        # Redis implementation would go here
        return 0
        
    async def _cleanup_database_events(self, retention_days: int) -> int:
        """Clean up old events from database."""
        # Database implementation would go here
        return 0