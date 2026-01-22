import unittest
from game.event_pool import EventPool
from schemas.orchestration import Event, EventTypes


class TestEventPool(unittest.TestCase):
    def setUp(self):
        self.event_pool = EventPool()
        
    def test_add_and_get_events(self):
        """Test adding events and retrieving them."""
        event1 = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Sword",
            event_target="New Location",
            description="Player1 moved to new location"
        )
        
        event2 = Event(
            event_type=EventTypes.ITEM_PICKUP,
            event_initiator="Player2",
            event_subject="Potion",
            event_target="Player2",
            description="Player2 picked up a potion"
        )
        
        self.event_pool.add_event(event1)
        self.event_pool.add_event(event2)
        
        events = self.event_pool.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], event1)
        self.assertEqual(events[1], event2)
        
    def test_get_events_with_limit(self):
        """Test retrieving events with a limit."""
        for i in range(5):
            event = Event(
                event_type=EventTypes.LOCATION_CHANGE,
                event_initiator=f"Player{i}",
                event_subject="Item",
                event_target=f"Location{i}",
                description=f"Event {i}"
            )
            self.event_pool.add_event(event)
        
        events = self.event_pool.get_events(limit=3)
        self.assertEqual(len(events), 3)
        
    def test_get_events_by_type(self):
        """Test filtering events by type."""
        location_event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )
        
        item_event = Event(
            event_type=EventTypes.ITEM_PICKUP,
            event_initiator="Player2",
            event_subject="Potion",
            event_target="Player2",
            description="Picked up a potion"
        )
        
        self.event_pool.add_event(location_event)
        self.event_pool.add_event(item_event)
        
        location_events = self.event_pool.get_events_by_type(EventTypes.LOCATION_CHANGE)
        self.assertEqual(len(location_events), 1)
        self.assertEqual(location_events[0], location_event)
        
        item_events = self.event_pool.get_events_by_type(EventTypes.ITEM_PICKUP)
        self.assertEqual(len(item_events), 1)
        self.assertEqual(item_events[0], item_event)
    
    def test_subscribe_and_queue_access(self):
        """Test subscribing to events and accessing the queue."""
        # Subscribe with a unique ID
        subscriber_queue = self.event_pool.subscribe("player1")
        
        event = Event(
            event_type=EventTypes.CHARACTER_MOVEMENT,
            event_initiator="Player1",
            event_subject="Character",
            event_target="North",
            description="Character moved north"
        )
        
        self.event_pool.add_event(event)
        
        # Check that the event is in the subscriber's queue
        self.assertEqual(subscriber_queue.size(), 1)
        queued_event = subscriber_queue.get()
        self.assertEqual(queued_event, event)
        self.assertTrue(subscriber_queue.empty())
        
    def test_multiple_subscribers_have_separate_queues(self):
        """Test that multiple subscribers have separate queues."""
        queue1 = self.event_pool.subscribe("player1")
        queue2 = self.event_pool.subscribe("player2")
        
        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )
        
        self.event_pool.add_event(event)
        
        # Both queues should have the event
        self.assertEqual(queue1.size(), 1)
        self.assertEqual(queue2.size(), 1)
        
        # Each queue should return the same event
        event1 = queue1.get()
        event2 = queue2.get()
        self.assertEqual(event1, event)
        self.assertEqual(event2, event)
        
        # Both queues should now be empty
        self.assertTrue(queue1.empty())
        self.assertTrue(queue2.empty())
        
    def test_event_history_for_new_subscribers(self):
        """Test that new subscribers get all previous events."""
        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )
        
        self.event_pool.add_event(event)
        
        # Subscribe after the event was added
        queue = self.event_pool.subscribe("player1")
        
        # The queue should contain the previous event
        self.assertEqual(queue.size(), 1)
        queued_event = queue.get()
        self.assertEqual(queued_event, event)
        
    def test_event_count(self):
        """Test getting the event count."""
        self.assertEqual(self.event_pool.get_event_count(), 0)
        
        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )
        
        self.event_pool.add_event(event)
        self.assertEqual(self.event_pool.get_event_count(), 1)
        
        self.event_pool.clear_events()
        self.assertEqual(self.event_pool.get_event_count(), 0)
        
    def test_subscriber_count(self):
        """Test getting the subscriber count."""
        self.assertEqual(self.event_pool.get_subscriber_count(), 0)

        self.event_pool.subscribe("player1")
        self.assertEqual(self.event_pool.get_subscriber_count(), 1)

        self.event_pool.subscribe("player2")
        self.assertEqual(self.event_pool.get_subscriber_count(), 2)

        self.event_pool.unsubscribe("player1")
        self.assertEqual(self.event_pool.get_subscriber_count(), 1)

    def test_publish_to_others_excludes_publisher(self):
        """Test that publish_to_others sends events to all subscribers except the publisher."""
        queue1 = self.event_pool.subscribe("player1")
        queue2 = self.event_pool.subscribe("player2")
        queue3 = self.event_pool.subscribe("player3")

        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )

        # Publish to others with player1 as publisher
        self.event_pool.publish_to_others("player1", event)

        # Player1's queue should be empty (publisher is excluded)
        self.assertEqual(queue1.size(), 0)

        # Player2 and Player3 should have received the event
        self.assertEqual(queue2.size(), 1)
        self.assertEqual(queue3.size(), 1)

        # Verify the events in the other queues
        event2 = queue2.get()
        event3 = queue3.get()
        self.assertEqual(event2, event)
        self.assertEqual(event3, event)
        self.assertTrue(queue2.empty())
        self.assertTrue(queue3.empty())

    def test_publish_to_others_adds_to_global_history(self):
        """Test that publish_to_others also adds to global event history."""
        self.event_pool.subscribe("player1")
        self.event_pool.subscribe("player2")

        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )

        # Publish to others
        self.event_pool.publish_to_others("player1", event)

        # Check that the event is in global history
        global_events = self.event_pool.get_events()
        self.assertEqual(len(global_events), 1)
        self.assertEqual(global_events[0], event)

    def test_subscriber_queue_publish_to_others(self):
        """Test that SubscriberQueue has a publish_to_others method."""
        queue1 = self.event_pool.subscribe("player1")
        queue2 = self.event_pool.subscribe("player2")
        queue3 = self.event_pool.subscribe("player3")

        # Verify that the method exists
        self.assertTrue(hasattr(queue1, 'publish_to_others'))

        event = Event(
            event_type=EventTypes.LOCATION_CHANGE,
            event_initiator="Player1",
            event_subject="Location",
            event_target="New Location",
            description="Moved to new location"
        )

        # Use the method from the subscriber queue
        queue1.publish_to_others(event)

        # Player1's queue should be empty (publisher is excluded)
        self.assertEqual(queue1.size(), 0)

        # Player2 and Player3 should have received the event
        self.assertEqual(queue2.size(), 1)
        self.assertEqual(queue3.size(), 1)

        # Verify the events in the other queues
        event2 = queue2.get()
        event3 = queue3.get()
        self.assertEqual(event2, event)
        self.assertEqual(event3, event)
        self.assertTrue(queue2.empty())
        self.assertTrue(queue3.empty())


if __name__ == '__main__':
    unittest.main()