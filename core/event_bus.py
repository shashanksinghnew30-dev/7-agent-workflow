"""
Thread-safe Event Bus for real-time telemetry streaming to CLI and Browser UI.
"""

from __future__ import annotations
import threading
import queue
from typing import Callable, List, Dict, Any
from core.models import EventMessage


class EventBus:
    """
    Central publish-subscribe event dispatcher.
    Enables decoupled telemetry streaming from Agents to Python Terminal and Browser UI.
    """

    def __init__(self):
        self._subscribers: List[Callable[[EventMessage], None]] = []
        self._client_queues: Dict[str, queue.Queue] = {}
        self._history: List[EventMessage] = []
        self._lock = threading.RLock()

    def subscribe(self, callback: Callable[[EventMessage], None]) -> None:
        """Register a synchronous callback subscriber (e.g. CLI logger)."""
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[EventMessage], None]) -> None:
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def register_client_queue(self, client_id: str) -> queue.Queue:
        """Register a FIFO queue for a streaming HTTP/SSE browser client."""
        with self._lock:
            q = queue.Queue(maxsize=1000)
            self._client_queues[client_id] = q
            # Catch up client with existing event history
            for event in self._history:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    break
            return q

    def unregister_client_queue(self, client_id: str) -> None:
        """Remove a client queue when browser disconnects."""
        with self._lock:
            if client_id in self._client_queues:
                del self._client_queues[client_id]

    def publish(self, agent: str, event_type: str, message: str, payload: Dict[str, Any] = None) -> EventMessage:
        """Publish an event across all active subscribers and queues."""
        event = EventMessage(
            agent=agent,
            event_type=event_type,
            message=message,
            payload=payload or {}
        )
        with self._lock:
            self._history.append(event)
            # Notify direct subscribers
            for sub in list(self._subscribers):
                try:
                    sub(event)
                except Exception as ex:
                    print(f"[EventBus Error] Subscriber failed: {ex}")

            # Notify queue listeners (Web SSE clients)
            for cid, q in list(self._client_queues.items()):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    # Drop oldest if queue is congested
                    try:
                        q.get_nowait()
                        q.put_nowait(event)
                    except Exception:
                        pass

        return event

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve complete event history for session inspection."""
        with self._lock:
            return [e.to_dict() for e in self._history]

    def clear(self) -> None:
        """Reset event bus history."""
        with self._lock:
            self._history.clear()
            self._client_queues.clear()
