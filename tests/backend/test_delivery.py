"""
Tests for Delivery objects (GameDelivery and RESTAPIDelivery)

Tests the complete player action processing pipeline:
1. Action submission → Orchestrator classification → Verdict
2. Event execution through manipulator
3. MAGG narrative generation via handle_events()
4. Response broadcasting
"""
import pytest
from unittest.mock import MagicMock, patch

from core.schemas.orchestration import (
    Event, EventTypes, OrchestrationVerdict, OrchestrationVerdictType,
    UserInteractionProcessing, UserInterationType
)
from core.schemas.in_game import Character, CharacterClass, AbilityScores, Coordinate2D


# ===================================================================
# Mock Setup
# ===================================================================

@pytest.fixture
def mock_character():
    """Create a mock character for testing."""
    return Character(
        name="Test Character",
        race="Human",
        char_class=CharacterClass.FIGHTER,
        level=1,
        backstory_summary="A brave warrior",
        personality_traits=["Brave"],
        max_hp=30,
        current_hp=30,
        temp_hp=0,
        armor_class=15,
        speed=30,
        stats=AbilityScores(
            strength=15, dexterity=12, constitution=14,
            intelligence=10, wisdom=10, charisma=10
        ),
        inventory=[],
        active_conditions_list=[],
        resources={},
        position=Coordinate2D(x=0.0, y=0.0),
        abilities=[],
    )


@pytest.fixture
def mock_player(mock_character):
    """Create a mock player entity."""
    player = MagicMock()
    player.character = mock_character
    return player


@pytest.fixture
def mock_session(mock_character, mock_player):
    """Create a mock session with all required components."""
    session = MagicMock()
    session.players = [mock_player]
    session.npcs = []
    session.current_scene = MagicMock()
    session.current_scene.name = "Test Scene"
    session.current_scene.description = "A test location"
    session.logger = MagicMock()
    session.logger.info = MagicMock()
    session.logger.warning = MagicMock()
    session.logger.error = MagicMock()
    session.logger.debug = MagicMock()
    return session


# ===================================================================
# RESTAPIDelivery Tests
# ===================================================================

class TestRESTAPIDelivery:
    """Test RESTAPIDelivery player action processing."""

    @pytest.fixture
    def rest_api_delivery(self, mock_session):
        """Create RESTAPIDelivery instance with mocked dependencies."""
        from backend.src.delivery.rest_api_delivery import RESTAPIDelivery
        from core.game.event_pool import SubscriberQueue
        
        event_queue = MagicMock(spec=SubscriberQueue)
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        logger.debug = MagicMock()
        
        delivery = RESTAPIDelivery(
            event_queue=event_queue,
            logger=logger,
            session_id="test-session-123"
        )
        delivery._session = mock_session
        return delivery

    def test_process_player_action_allowed(self, rest_api_delivery, mock_session, mock_player):
        """Test processing an allowed player action."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.request.return_value = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Test Character looks around"
        )
        mock_orchestrator.character_action_story.return_value = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.ALLOWED_PLAYER_ACTION,
            details="You look around the dimly lit tavern...",
            original_request="where am i"
        )
        mock_session.orchestrator = mock_orchestrator

        # Mock manipulator
        mock_manipulator = MagicMock()
        mock_manipulator._external_action_as_an_entity.return_value = [
            Event(
                event_type=EventTypes.ACTION_RESULT,
                event_initiator="Test Character",
                description="Character looks around"
            )
        ]
        mock_manipulator.execute_events.return_value = []
        mock_session.manipulator = mock_manipulator

        # Mock MAGG (game_master)
        async def mock_handle_events():
            return "You find yourself in a cozy tavern..."
        
        mock_game_master = MagicMock()
        mock_game_master.handle_events = mock_handle_events
        mock_session.game_master = mock_game_master

        # Mock delivery methods
        rest_api_delivery.master_message = MagicMock()
        rest_api_delivery.session_updated = MagicMock()

        # Execute
        result = rest_api_delivery.process_player_action(
            character_name="Test Character",
            action_text="where am i"
        )

        # Verify
        assert result['success'] is True
        assert result['status'] == 'processed'
        assert 'dm_response' in result
        rest_api_delivery.master_message.assert_called_once()

    def test_process_player_action_clarification_needed(self, rest_api_delivery, mock_session, mock_player):
        """Test processing when clarification is needed."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.request.return_value = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Unclear action"
        )
        mock_orchestrator.character_action_story.return_value = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.CLAIRIFICATION_NEEDED,
            details="Could you clarify what you want to do?",
            original_request="do thing"
        )
        mock_session.orchestrator = mock_orchestrator

        # Mock MAGG clarify method
        mock_game_master = MagicMock()
        mock_game_master.clarify_user_request.return_value = "Could you clarify your intention?"
        mock_session.game_master = mock_game_master

        # Mock delivery methods
        rest_api_delivery.master_message = MagicMock()
        rest_api_delivery.session_updated = MagicMock()

        # Execute
        result = rest_api_delivery.process_player_action(
            character_name="Test Character",
            action_text="do thing"
        )

        # Verify
        assert result['status'] == 'processed'
        mock_game_master.clarify_user_request.assert_called_once()

    def test_process_player_action_illegal(self, rest_api_delivery, mock_session, mock_player):
        """Test processing an illegal player action."""
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.request.return_value = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Illegal action"
        )
        mock_orchestrator.character_action_story.return_value = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION,
            details="You cannot do that in combat",
            original_request="illegal action"
        )
        mock_session.orchestrator = mock_orchestrator

        # Mock MAGG illegal comment
        mock_game_master = MagicMock()
        mock_game_master.illegal_action_comment.return_value = "That action violates combat rules"
        mock_session.game_master = mock_game_master

        # Mock delivery methods
        rest_api_delivery.master_message = MagicMock()
        rest_api_delivery.session_updated = MagicMock()

        # Execute
        result = rest_api_delivery.process_player_action(
            character_name="Test Character",
            action_text="illegal action"
        )

        # Verify
        assert result['status'] == 'processed'
        mock_game_master.illegal_action_comment.assert_called_once()

    def test_process_player_action_character_not_found(self, rest_api_delivery, mock_session):
        """Test processing when character is not found."""
        mock_session.players = []  # No players

        result = rest_api_delivery.process_player_action(
            character_name="Unknown Character",
            action_text="test action"
        )

        assert result['error'] == 'Character Unknown Character not found'
        assert result['status'] == 'error'

    def test_process_player_action_no_orchestrator(self, rest_api_delivery, mock_session):
        """Test processing when orchestrator is not available."""
        mock_session.orchestrator = None

        result = rest_api_delivery.process_player_action(
            character_name="Test Character",
            action_text="test action"
        )

        assert result['error'] == 'Orchestrator not available'
        assert result['status'] == 'error'


# ===================================================================
# GameDelivery Tests (Sync wrappers for async methods)
# ===================================================================

class TestGameDelivery:
    """Test GameDelivery player action processing."""

    @pytest.fixture
    def game_delivery(self, mock_session):
        """Create GameDelivery instance with mocked dependencies."""
        from backend.src.delivery.game_delivery import GameDelivery
        from core.game.event_pool import SubscriberQueue
        
        event_queue = MagicMock(spec=SubscriberQueue)
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        logger.debug = MagicMock()
        
        delivery = GameDelivery(
            session_id="test-session-123",
            session=mock_session,
            event_queue=event_queue,
            logger=logger
        )
        return delivery

    def test_process_player_action_allowed_async(self, game_delivery, mock_session, mock_player):
        """Test processing of an allowed player action."""
        import asyncio
        
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.request.return_value = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Test Character attacks orc"
        )
        mock_orchestrator.character_action_story.return_value = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.ALLOWED_PLAYER_ACTION,
            details="Test Character swings their sword",
            original_request="I attack the orc"
        )
        mock_session.orchestrator = mock_orchestrator

        # Mock manipulator
        mock_manipulator = MagicMock()
        mock_manipulator._external_action_as_an_entity.return_value = []
        mock_manipulator.execute_events.return_value = []
        mock_session.manipulator = mock_manipulator

        # Mock MAGG (game_master) - sync comment method
        mock_game_master = MagicMock()
        mock_game_master.comment.return_value = "You swing your sword at the orc!"
        mock_session.game_master = mock_game_master

        # Mock delivery methods
        game_delivery.master_message = MagicMock()
        game_delivery.session_updated = MagicMock()

        # Execute (process_player_action is async, so we run it)
        async def run_test():
            return await game_delivery.process_player_action(
                character_name="Test Character",
                action_text="I attack the orc"
            )
        
        result = asyncio.run(run_test())

        # Verify
        assert result['success'] is True
        assert 'dm_response' in result
        game_delivery.master_message.assert_called_once()

    def test_process_player_action_clarification_async(self, game_delivery, mock_session, mock_player):
        """Test processing when clarification is needed."""
        import asyncio
        
        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.request.return_value = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Unclear"
        )
        mock_orchestrator.character_action_story.return_value = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.CLAIRIFICATION_NEEDED,
            details="Needs clarification",
            original_request="do something"
        )
        mock_session.orchestrator = mock_orchestrator

        # Mock MAGG
        mock_game_master = MagicMock()
        mock_game_master.clarify_user_request.return_value = "What exactly do you want to do?"
        mock_session.game_master = mock_game_master

        # Mock delivery methods
        game_delivery.master_message = MagicMock()
        game_delivery.session_updated = MagicMock()

        # Execute
        async def run_test():
            return await game_delivery.process_player_action(
                character_name="Test Character",
                action_text="do something"
            )
        
        result = asyncio.run(run_test())

        # Verify
        assert result['success'] is True
        assert 'dm_response' in result
        mock_game_master.clarify_user_request.assert_called_once()

    def test_process_player_action_character_not_found(self, game_delivery, mock_session):
        """Test processing when character is not found."""
        import asyncio
        
        mock_session.players = []

        async def run_test():
            return await game_delivery.process_player_action(
                character_name="Unknown",
                action_text="test"
            )
        
        result = asyncio.run(run_test())

        assert result['success'] is False
        assert 'error' in result
        assert 'not found' in result['error']


# ===================================================================
# Integration Tests
# ===================================================================

class TestDeliveryIntegration:
    """Test that delivery objects work correctly with real schemas."""

    def test_event_schema_creation(self):
        """Test that Event objects can be created correctly."""
        event = Event(
            event_type=EventTypes.ACTION_RESULT,
            event_initiator="Test Character",
            description="A test event"
        )
        
        assert event.event_type == EventTypes.ACTION_RESULT
        assert event.event_initiator == "Test Character"
        assert event.description == "A test event"

    def test_orchestration_verdict_schema(self):
        """Test OrchestrationVerdict creation and fields."""
        verdict = OrchestrationVerdict(
            verdict_type=OrchestrationVerdictType.ALLOWED_PLAYER_ACTION,
            details="Action allowed",
            original_request="test action"
        )
        
        assert verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION
        assert verdict.details == "Action allowed"
        assert verdict.original_request == "test action"

    def test_user_interaction_processing(self):
        """Test UserInteractionProcessing schema."""
        processing = UserInteractionProcessing(
            interaction_type=UserInterationType.CHARACTER_ACTION,
            user_request_saturated="Enhanced action description"
        )
        
        assert processing.interaction_type == UserInterationType.CHARACTER_ACTION
        assert processing.user_request_saturated == "Enhanced action description"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
