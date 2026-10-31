"""
Hub-and-Spoke Event Bus & Inter-Agent Protocol
Handles structured domain events between Subagents and the Parent Supervisor.
Streams live events to Server-Sent Events (SSE) subscribers.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Callable, Awaitable
from datetime import datetime, timezone

logger = logging.getLogger("event_bus")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self._sse_queues: List[asyncio.Queue] = []
        self._history: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Register a handler callback for an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def emit(self, event: Dict[str, Any]):
        """
        Emit a domain event to all registered subagents and push to live SSE queues.
        """
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"EventBus emit: [{event.get('event_type')}] from {event.get('source_agent')} -> {event.get('target_agent')}")
        self._history.append(event)
        if len(self._history) > 200:
            self._history.pop(0)

        # Notify direct subscribers
        event_type = event.get("event_type", "*")
        handlers = self._subscribers.get(event_type, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}")

        # Broadcast to active frontend SSE streams
        dead_queues = []
        for q in self._sse_queues:
            try:
                q.put_nowait(event)
            except Exception:
                dead_queues.append(q)
        for dq in dead_queues:
            self._sse_queues.remove(dq)

    def register_sse_listener(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._sse_queues.append(q)
        return q

    def remove_sse_listener(self, q: asyncio.Queue):
        if q in self._sse_queues:
            self._sse_queues.remove(q)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]


event_bus = EventBus()

