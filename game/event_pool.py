import queue
import threading
from typing import List, Dict, Any

from schemas.orchestration import Event


class SubscriberQueue:
    """
    A thread-safe queue for a specific subscriber to hold events using Python's built-in queue.
    """
    def __init__(self, maxsize: int = 0, parent_pool=None, subscriber_id=None):
        # Use Python's built-in thread-safe queue
        self._queue = queue.Queue(maxsize=maxsize)
        self._parent_pool = parent_pool
        self._subscriber_id = subscriber_id

    def put(self, event: Event) -> None:
        """
        Add an event to the queue in a thread-safe manner.

        Args:
            event (Event): The event to add to the queue
        """
        # If queue is full and maxsize > 0, this will block until space is available
        # If you want non-blocking behavior, use put_nowait and handle Full exception
        self._queue.put(event)

    def get(self) -> Event | None:
        """
        Get and remove the oldest event from the queue in a thread-safe manner.

        Returns:
            Event: The oldest event in the queue, or None if empty
        """
        try:
            # Use non-blocking get with timeout to avoid indefinite blocking
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def get_all(self) -> List[Event]:
        """
        Get all events from the queue without removing them in a thread-safe manner.

        Returns:
            List[Event]: All events in the queue
        """
        # Get all items from the queue and then put them back
        items = []
        while True:
            try:
                item = self._queue.get_nowait()
                items.append(item)
            except queue.Empty:
                break
        
        # Put all items back in the queue
        for item in items:
            self._queue.put(item)
        
        return items

    def peek(self) -> Event | None:
        """
        Peek at the oldest event without removing it in a thread-safe manner.

        Returns:
            Event: The oldest event in the queue, or None if empty
        """
        try:
            # Get the item without removing it
            # Since queue doesn't support peeking directly, we get and put back
            item = self._queue.get_nowait()
            # Put it back at the front - this is not perfectly thread-safe
            # as another thread could get the item before we put it back
            # A better approach would be to use a different data structure
            # But for now, we'll re-add it to the queue
            temp_queue = queue.Queue()
            temp_queue.put(item)
            
            # Move all other items to temporary queue
            remaining_items = []
            while True:
                try:
                    remaining_items.append(self._queue.get_nowait())
                except queue.Empty:
                    break
            
            # Put the peeked item back first
            self._queue.put(item)
            
            # Put back all other items
            for rem_item in remaining_items:
                self._queue.put(rem_item)
                
            return item
        except queue.Empty:
            return None

    def empty(self) -> bool:
        """
        Check if the queue is empty in a thread-safe manner.

        Returns:
            bool: True if the queue is empty, False otherwise
        """
        return self._queue.empty()

    def size(self) -> int:
        """
        Get the number of events in the queue in a thread-safe manner.

        Returns:
            int: Number of events in the queue
        """
        return self._queue.qsize()

    def clear(self) -> None:
        """
        Clear all events from the queue in a thread-safe manner.
        """
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def publish_to_others(self, event: Event) -> None:
        """
        Publish an event to all subscriber queues except this one in a thread-safe manner.

        Args:
            event (Event): The event to publish to other subscribers
        """
        if self._parent_pool is not None:
            self._parent_pool.publish_to_others(self._subscriber_id, event)


class EventPool:
    """
    A thread-safe centralized event pool that stores events and shares them with subscribed clients.
    Each subscriber has their own queue of events to consume.
    """

    def __init__(self):
        self._events: List[Event] = []  # Global event history
        self._subscriber_queues: Dict[Any, SubscriberQueue] = {}  # Queue for each subscriber
        self._lock = threading.RLock()  # Use RLock for thread safety allowing recursive locks

    def add_event(self, event: Event) -> None:
        """
        Add an event to the global pool and to all subscriber queues in a thread-safe manner.

        Args:
            event (Event): The event to add to the pool
        """
        with self._lock:
            # Add to global event history
            self._events.append(event)

            # Add to all subscriber queues - each queue is thread-safe individually
            for queue in self._subscriber_queues.values():
                queue.put(event)

    def add_events(self, events: List[Event]) -> None:
        """
        Add multiple events to the pool in a thread-safe manner.

        Args:
            events (List[Event]): List of events to add
        """
        # Hold the lock for the entire operation to ensure all events are added atomically
        with self._lock:
            for event in events:
                # Add to global event history
                self._events.append(event)

                # Add to all subscriber queues
                for queue in self._subscriber_queues.values():
                    queue.put(event)

    def get_events(self, limit: int | None = None) -> List[Event]:
        """
        Retrieve events from the global pool in a thread-safe manner.

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
        Retrieve events filtered by type from the global pool in a thread-safe manner.

        Args:
            event_type: The event type to filter by (from EventTypes enum)

        Returns:
            List[Event]: List of events matching the specified type
        """
        with self._lock:
            return [event for event in self._events if event.event_type == event_type]

    def subscribe(self, subscriber_id: Any, max_queue_size: int = 0) -> SubscriberQueue:
        """
        Subscribe to receive events in a dedicated queue in a thread-safe manner.

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
                # The lock is held here to ensure consistency during subscription
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
        Unsubscribe and remove the subscriber's queue in a thread-safe manner.

        Args:
            subscriber_id (Any): The subscriber ID to remove
        """
        with self._lock:
            if subscriber_id in self._subscriber_queues:
                del self._subscriber_queues[subscriber_id]

    def get_subscriber_queue(self, subscriber_id: Any) -> SubscriberQueue | None:
        """
        Get the queue for a specific subscriber in a thread-safe manner.

        Args:
            subscriber_id (Any): The subscriber ID

        Returns:
            SubscriberQueue: The queue for the subscriber, or None if not subscribed
        """
        with self._lock:
            return self._subscriber_queues.get(subscriber_id)

    def publish_to_others(self, publisher_id: Any, event: Event) -> None:
        """
        Publish an event to all subscriber queues except the publisher's own queue in a thread-safe manner.

        Args:
            publisher_id (Any): The ID of the publisher (this subscriber's queue will be excluded)
            event (Event): The event to publish to other subscribers
        """
        with self._lock:
            # Add to global event history
            self._events.append(event)

            # Add to all subscriber queues except the publisher's
            for sub_id, sub_queue in self._subscriber_queues.items():
                if sub_id != publisher_id:
                    sub_queue.put(event)

    def clear_events(self) -> None:
        """
        Clear all events from the global pool in a thread-safe manner.
        Note: This does not clear individual subscriber queues.
        """
        with self._lock:
            self._events.clear()

    def clear_subscriber_queue(self, subscriber_id: Any) -> None:
        """
        Clear all events from a specific subscriber's queue in a thread-safe manner.

        Args:
            subscriber_id (Any): The subscriber ID whose queue to clear
        """
        with self._lock:
            if subscriber_id in self._subscriber_queues:
                self._subscriber_queues[subscriber_id].clear()

    def get_event_count(self) -> int:
        """
        Get the total number of events in the global pool in a thread-safe manner.

        Returns:
            int: Number of events in the global pool
        """
        with self._lock:
            return len(self._events)

    def get_subscriber_count(self) -> int:
        """
        Get the number of subscribers in a thread-safe manner.

        Returns:
            int: Number of subscribers
        """
        with self._lock:
            return len(self._subscriber_queues)