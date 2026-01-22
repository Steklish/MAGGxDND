from typing import List, Callable, Dict, Any
from schemas.orchestration import Event
import threading
from collections import deque


class SubscriberQueue:
    """
    A queue for a specific subscriber to hold events.
    """
    def __init__(self, maxsize: int = 0, parent_pool=None, subscriber_id=None):
        self._queue = deque()
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._parent_pool = parent_pool
        self._subscriber_id = subscriber_id

    def put(self, event: Event) -> None:
        """
        Add an event to the queue.

        Args:
            event (Event): The event to add to the queue
        """
        with self._lock:
            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                # Remove oldest event if queue is full
                self._queue.popleft()
            self._queue.append(event)

    def get(self) -> Event | None:
        """
        Get and remove the oldest event from the queue.

        Returns:
            Event: The oldest event in the queue
        """
        with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def get_all(self) -> List[Event]:
        """
        Get all events from the queue without removing them.

        Returns:
            List[Event]: All events in the queue
        """
        with self._lock:
            return list(self._queue)

    def peek(self) -> Event | None:
        """
        Peek at the oldest event without removing it.

        Returns:
            Event: The oldest event in the queue, or None if empty
        """
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None

    def empty(self) -> bool:
        """
        Check if the queue is empty.

        Returns:
            bool: True if the queue is empty, False otherwise
        """
        with self._lock:
            return len(self._queue) == 0

    def size(self) -> int:
        """
        Get the number of events in the queue.

        Returns:
            int: Number of events in the queue
        """
        with self._lock:
            return len(self._queue)

    def clear(self) -> None:
        """
        Clear all events from the queue.
        """
        with self._lock:
            self._queue.clear()

    def publish_to_others(self, event: Event) -> None:
        """
        Publish an event to all subscriber queues except this one.

        Args:
            event (Event): The event to publish to other subscribers
        """
        if self._parent_pool is not None:
            self._parent_pool.publish_to_others(self._subscriber_id, event)


class EventPool:
    """
    A centralized event pool that stores events and shares them with subscribed clients.
    Each subscriber has their own queue of events to consume.
    """

    def __init__(self):
        self._events: List[Event] = []  # Global event history
        self._subscriber_queues: Dict[Any, SubscriberQueue] = {}  # Queue for each subscriber
        self._lock = threading.RLock()  # Use RLock for thread safety

    def add_event(self, event: Event) -> None:
        """
        Add an event to the global pool and to all subscriber queues.

        Args:
            event (Event): The event to add to the pool
        """
        with self._lock:
            # Add to global event history
            self._events.append(event)

            # Add to all subscriber queues
            for queue in self._subscriber_queues.values():
                queue.put(event)

    def add_events(self, events: List[Event]) -> None:
        """
        Add multiple events to the pool.

        Args:
            events (List[Event]): List of events to add
        """
        for event in events:
            self.add_event(event)

    def get_events(self, limit: int | None = None) -> List[Event]:
        """
        Retrieve events from the global pool.

        Args:
            limit (int, optional): Maximum number of events to return (most recent first)

        Returns:
            List[Event]: List of events, optionally limited
        """
        with self._lock:
            if limit is None:
                return self._events.copy()  # Return a copy to prevent external modification
            else:
                return self._events[-limit:].copy()  # Return the most recent events up to the limit

    def get_events_by_type(self, event_type) -> List[Event]:
        """
        Retrieve events filtered by type from the global pool.

        Args:
            event_type: The event type to filter by (from EventTypes enum)

        Returns:
            List[Event]: List of events matching the specified type
        """
        with self._lock:
            return [event for event in self._events if event.event_type == event_type]

    def subscribe(self, subscriber_id: Any, max_queue_size: int = 0) -> SubscriberQueue:
        """
        Subscribe to receive events in a dedicated queue.

        Args:
            subscriber_id (Any): Unique identifier for the subscriber
            max_queue_size (int): Maximum size of the subscriber's queue (0 for unlimited)

        Returns:
            SubscriberQueue: The queue for this subscriber
        """
        with self._lock:
            if subscriber_id not in self._subscriber_queues:
                queue = SubscriberQueue(maxsize=max_queue_size, parent_pool=self, subscriber_id=subscriber_id)
                self._subscriber_queues[subscriber_id] = queue

                # Add any existing events to the new subscriber's queue
                for event in self._events:
                    queue.put(event)

                return queue
            else:
                # Update the parent pool and subscriber ID for existing queue
                existing_queue = self._subscriber_queues[subscriber_id]
                existing_queue._parent_pool = self
                existing_queue._subscriber_id = subscriber_id
                return existing_queue

    def unsubscribe(self, subscriber_id: Any) -> None:
        """
        Unsubscribe and remove the subscriber's queue.

        Args:
            subscriber_id (Any): The subscriber ID to remove
        """
        with self._lock:
            if subscriber_id in self._subscriber_queues:
                del self._subscriber_queues[subscriber_id]

    def get_subscriber_queue(self, subscriber_id: Any) -> SubscriberQueue | None:
        """
        Get the queue for a specific subscriber.

        Args:
            subscriber_id (Any): The subscriber ID

        Returns:
            SubscriberQueue: The queue for the subscriber, or None if not subscribed
        """
        with self._lock:
            return self._subscriber_queues.get(subscriber_id)

    def publish_to_others(self, publisher_id: Any, event: Event) -> None:
        """
        Publish an event to all subscriber queues except the publisher's own queue.

        Args:
            publisher_id (Any): The ID of the publisher (this subscriber's queue will be excluded)
            event (Event): The event to publish to other subscribers
        """
        with self._lock:
            # Add to global event history
            self._events.append(event)

            # Add to all subscriber queues except the publisher's
            for sub_id, queue in self._subscriber_queues.items():
                if sub_id != publisher_id:
                    queue.put(event)

    def clear_events(self) -> None:
        """
        Clear all events from the global pool.
        Note: This does not clear individual subscriber queues.
        """
        with self._lock:
            self._events.clear()

    def clear_subscriber_queue(self, subscriber_id: Any) -> None:
        """
        Clear all events from a specific subscriber's queue.

        Args:
            subscriber_id (Any): The subscriber ID whose queue to clear
        """
        with self._lock:
            if subscriber_id in self._subscriber_queues:
                self._subscriber_queues[subscriber_id].clear()

    def get_event_count(self) -> int:
        """
        Get the total number of events in the global pool.

        Returns:
            int: Number of events in the global pool
        """
        with self._lock:
            return len(self._events)

    def get_subscriber_count(self) -> int:
        """
        Get the number of subscribers.

        Returns:
            int: Number of subscribers
        """
        with self._lock:
            return len(self._subscriber_queues)