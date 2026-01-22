#!/usr/bin/env python3
"""
Simple demonstration of the EventPool functionality.
"""

from game.event_pool import EventPool
from schemas.orchestration import Event, EventTypes


def main():
    # Create an event pool
    event_pool = EventPool()

    # Subscribe a few clients
    player1_queue = event_pool.subscribe("player1")
    player2_queue = event_pool.subscribe("player2")
    dm_queue = event_pool.subscribe("dm")

    print("=== Testing regular event distribution ===")
    # Add some events using the regular add_event method
    event1 = Event(
        event_type=EventTypes.LOCATION_CHANGE,
        event_initiator="Orc",
        event_subject="Orc Chief",
        event_target="Cave Entrance",
        description="The Orc Chief moves to the cave entrance."
    )

    event2 = Event(
        event_type=EventTypes.ITEM_PICKUP,
        event_initiator="Player",
        event_subject="Magic Sword",
        event_target="Player Inventory",
        description="The player picks up a magic sword."
    )

    print("Adding events to the pool using add_event (all subscribers receive)...")
    event_pool.add_event(event1)
    event_pool.add_event(event2)

    print(f"Global event count: {event_pool.get_event_count()}")
    print(f"Subscriber count: {event_pool.get_subscriber_count()}")

    print("\nPlayer1 queue size:", player1_queue.size())  # Should be 2
    print("Player2 queue size:", player2_queue.size())    # Should be 2
    print("DM queue size:", dm_queue.size())              # Should be 2

    # Clear queues for next test
    while not player1_queue.empty():
        player1_queue.get()
    while not player2_queue.empty():
        player2_queue.get()
    while not dm_queue.empty():
        dm_queue.get()

    print("\n=== Testing publish_to_others functionality ===")
    # Now test the publish_to_others method
    secret_event = Event(
        event_type=EventTypes.CHARACTER_STATUS_CHANGE,
        event_initiator="DM",
        event_subject="Dragon",
        event_target="Hidden Chamber",
        description="The Dragon secretly prepares an ambush."
    )

    print("Publishing event to others (DM won't receive it back)...")
    event_pool.publish_to_others("dm", secret_event)

    print(f"Global event count after publish_to_others: {event_pool.get_event_count()}")

    print("\nPlayer1 queue size:", player1_queue.size())  # Should be 1 (received the secret event)
    print("Player2 queue size:", player2_queue.size())    # Should be 1 (received the secret event)
    print("DM queue size:", dm_queue.size())              # Should be 0 (was excluded)

    print("\nRetrieving events from Player1's queue:")
    for i in range(player1_queue.size()):
        event = player1_queue.get()
        if event:
            print(f"  Event {i+1}: {event.description}")

    print("\nRetrieving events from Player2's queue:")
    for i in range(player2_queue.size()):
        event = player2_queue.get()
        if event:
            print(f"  Event {i+1}: {event.description}")

    print("\nRetrieving events from DM's queue:")
    for i in range(dm_queue.size()):
        event = dm_queue.get()
        if event:
            print(f"  Event {i+1}: {event.description}")
    if dm_queue.size() == 0:
        print("  DM received no events (correctly excluded)")

    print("\n=== Testing publish_to_others from SubscriberQueue ===")
    # Test publishing from the subscriber queue directly
    announcement_event = Event(
        event_type=EventTypes.LOCATION_STATUS_CHANGE,
        event_initiator="player1",
        event_subject="Town Gate",
        event_target="Closed",
        description="Player1 announces that the town gate is now closed."
    )

    print("Player1 publishing event to others using their own queue...")
    player1_queue.publish_to_others(announcement_event)

    print(f"Global event count after publish from queue: {event_pool.get_event_count()}")

    print("\nPlayer1 queue size:", player1_queue.size())  # Should be 0 (was excluded)
    print("Player2 queue size:", player2_queue.size())    # Should be 1 (received the announcement)
    print("DM queue size:", dm_queue.size())              # Should be 1 (received the announcement)

    # Clear Player2 and DM queues to show the announcement event
    announcement_from_player2 = player2_queue.get() if player2_queue.size() > 0 else None
    announcement_from_dm = dm_queue.get() if dm_queue.size() > 0 else None

    if announcement_from_player2:
        print(f"\nPlayer2 received: {announcement_from_player2.description}")
    if announcement_from_dm:
        print(f"DM received: {announcement_from_dm.description}")


if __name__ == "__main__":
    main()