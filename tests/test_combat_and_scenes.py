import pytest
from unittest.mock import MagicMock
from core.schemas.in_game import Character, NPCCharacter, SceneNode, GameModes, Coordinate2D, AbilityScores, CharacterClass
from core.schemas.orchestration import Event, EventTypes
from core.game.engine import Session
from core.game.event_pool import EventPool
from core.interface.delivery import Delivery, Request


class DummyDelivery(Delivery):
    def __init__(self, eq, logger):
        super().__init__(eq, logger)
        self.master_messages = []
        self.session_updates = []

    def master_message(self, text: str, tag: str | None = None):
        self.master_messages.append((text, tag))

    def player_request(self, character: Character) -> str:
        req = self.get_first_request_by_player(character.name)
        return req.request_text if req else ""

    def choose_player(self, session: "Session"):
        return session.players[0] if session.players else None

    def session_updated(self, session: "Session") -> None:
        self.session_updates.append(session.get_session_state())


def test_combat_mode_switch():
    event_pool = EventPool()
    delivery_queue = event_pool.subscribe("delivery")
    logger = MagicMock()
    delivery = DummyDelivery(delivery_queue, logger)

    session = Session(
        session_name="CombatTest",
        chroma_client=MagicMock(),
        logger=logger,
        generator=MagicMock(),
        event_pool=event_pool,
        delivery=delivery,
        language="en"
    )

    # Initial state should be STORY
    assert session.game_mode == GameModes.STORY

    # Trigger enter_combat
    session.enter_combat(reason="Ambush by goblins!")
    assert session.game_mode == GameModes.COMBAT
    assert len(delivery.master_messages) >= 1
    assert "COMBAT INITIATED" in delivery.master_messages[-1][0]

    # Verify session state serialization includes game_mode
    state = session.get_session_state()
    assert state["game_mode"] == "COMBAT"

    # Trigger exit_combat
    session.exit_combat(reason="All goblins slain!")
    assert session.game_mode == GameModes.STORY
    assert "COMBAT CONCLUDED" in delivery.master_messages[-1][0]
    assert session.get_session_state()["game_mode"] == "STORY"


def test_turn_queue_serialization_format():
    event_pool = EventPool()
    delivery_queue = event_pool.subscribe("delivery")
    logger = MagicMock()
    delivery = DummyDelivery(delivery_queue, logger)

    session = Session(
        session_name="TurnQueueTest",
        chroma_client=MagicMock(),
        logger=logger,
        generator=MagicMock(),
        event_pool=event_pool,
        delivery=delivery,
        language="en"
    )

    stats = AbilityScores(strength=14, dexterity=14, constitution=12, intelligence=10, wisdom=10, charisma=10)
    hero = Character(name="Valeros", race="Human", char_class=CharacterClass.FIGHTER, level=1, backstory_summary="", personality_traits=[], max_hp=12, current_hp=12, temp_hp=0, armor_class=16, speed=30, stats=stats)
    
    player_mock = MagicMock()
    player_mock.character = hero
    session.players = [player_mock]

    # Add to turn queue
    session.turn_queue = [(player_mock, 0.0, 5.0)]

    state = session.get_session_state()
    tq = state["turn_queue"]
    assert len(tq) == 1
    assert isinstance(tq[0], dict)
    assert tq[0]["character"] == "Valeros"
    assert tq[0]["next_turn"] == 5.0
    assert tq[0]["time_added"] == 0.0


def test_delivery_has_request_from_player():
    event_pool = EventPool()
    delivery_queue = event_pool.subscribe("delivery")
    logger = MagicMock()
    delivery = DummyDelivery(delivery_queue, logger)

    assert delivery.has_request_from_player("Valeros") is False

    delivery.put_request(Request(player_id="Valeros", request_text="I swing my longsword", timestamp=100.0))

    assert delivery.has_request_from_player("Valeros") is True
    assert delivery.has_request_from_player("Kyra") is False

    # Check that has_request_from_player did NOT consume the request
    req = delivery.get_first_request_by_player("Valeros")
    assert req is not None
    assert req.request_text == "I swing my longsword"
    assert delivery.has_request_from_player("Valeros") is False
