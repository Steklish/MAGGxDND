"""
AI Game Service - Bridge between Backend API and Core Game Engine & MAGG.
Implements the requirements defined in core/BACKEND_INTEGRATION_REQUIREMENTS.md.
"""
from typing import List, Optional, Dict, Any
import logging
import uuid
import asyncio

from core.game.engine import Session
from core.schemas.orchestration import (
    Event,
    EventTypes,
    Message,
    UserInterationType,
    OrchestrationVerdictType,
)
from core.schemas.in_game import SceneNode, Character
from backend.src.game.session_factory import session_factory
from backend.src.services.ai_game_exceptions import (
    AIServiceError,
    GenerationError,
    SessionNotInitializedError,
    CharacterNotFoundError,
    InvalidActionError,
)

logger = logging.getLogger(__name__)


class AIGameService:
    """
    Coordinates AI-driven game orchestration, procedural/Gemini scene and entity generation,
    and narrative delivery through MAGG and Session Engine.
    """

    def __init__(self, session: Session):
        self.session = session

    async def initialize_session(
        self,
        scene_prompt: Optional[str] = None,
        character_prompts: Optional[List[str]] = None,
        npc_prompts: Optional[List[str]] = None,
        wishes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize the session with scene, characters, and NPCs.
        """
        if not self.session:
            raise SessionNotInitializedError("Session instance is null or not provided")

        scene_prompt = scene_prompt or wishes or "A mysterious adventure begins at a crossroads tavern..."
        character_prompts = character_prompts or []
        npc_prompts = npc_prompts or []

        try:
            # 1. Initialize Scene
            scene = session_factory.init_scene(self.session, scene_prompt)

            # 2. Initialize Player Characters
            created_characters = []
            for i, prompt in enumerate(character_prompts):
                player_name = f"Player_{i + 1}"
                player_id = str(uuid.uuid4())
                player = session_factory.init_player(self.session, prompt, player_name, player_id)
                created_characters.append(player)

            # 3. Initialize NPCs
            created_npcs = []
            for prompt in npc_prompts:
                npc = session_factory.init_npc(self.session, prompt)
                created_npcs.append(npc)

            # 4. Announce scene if delivery is available
            welcome_text = f"Welcome to {scene.name}! {scene.description}"
            if hasattr(self.session, 'delivery') and self.session.delivery:
                self.session.delivery.master_message(welcome_text, tag="Narrative")
                self.session.delivery.session_updated(self.session)

            return {
                "success": True,
                "session_id": getattr(self.session, 'session_id', str(uuid.uuid4())),
                "scene": {
                    "name": scene.name,
                    "description": scene.description,
                },
                "characters_count": len(self.session.players),
                "npcs_count": len(self.session.npcs),
                "message": f"Initialized with {len(self.session.players)} players and {len(self.session.npcs)} NPCs."
            }
        except Exception as e:
            logger.error(f"[AIGameService] Failed to initialize session: {e}", exc_info=True)
            raise GenerationError(f"Session initialization failed: {e}") from e

    async def process_player_action(
        self,
        character_name: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Process a player action through orchestrator, MAGG narrative commentary, and event execution.
        """
        if not self.session:
            raise SessionNotInitializedError("Session is not initialized")

        # Find character in players
        player = next((p for p in self.session.players if p.character.name.lower() == character_name.lower()), None)
        if not player:
            # Fallback search by username/key
            player = next((p for p in self.session.players if character_name.lower() in p.character.name.lower()), None)
            if not player:
                raise CharacterNotFoundError(f"Character '{character_name}' not found in active session")

        try:
            # Request interaction evaluation from orchestrator
            orchestrator = self.session.orchestrator
            interaction = orchestrator.request(
                username=player.character.name,
                request_text=action
            )

            dm_response = ""
            events = []

            if interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta question / rules query
                verdict = orchestrator.meta_interaction(player.character.name, action)
                dm_response = verdict.details or "The Dungeon Master ponders your question."
            else:
                # In-game character action
                verdict = (
                    orchestrator.character_action_combat(player, action, interaction)
                    if getattr(self.session, 'game_mode', None) == "COMBAT"
                    else orchestrator.character_action_story(player, action, interaction)
                )

                if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    action_text = verdict.details or action
                    action_events = self.session.manipulator._external_action_as_an_entity(action_text, player)
                    executed = self.session.manipulator.execute_events(action_events)
                    events = executed if executed else action_events

                    # MAGG narrative commentary
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        try:
                            dm_response = self.session.game_master.comment(events)
                        except Exception as m_err:
                            logger.warning(f"[AIGameService] MAGG comment error: {m_err}")
                            dm_response = f"{player.character.name} performs: {action}"
                    else:
                        dm_response = f"{player.character.name} performs: {action}"

                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        dm_response = self.session.game_master.clarify_user_request(verdict.details or "Action unclear.")
                    else:
                        dm_response = verdict.details or "Could you clarify your action?"

                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    if hasattr(self.session, 'game_master') and self.session.game_master:
                        dm_response = self.session.game_master.illegal_action_comment(
                            prompt=action,
                            name=player.character.name,
                            reasoning=verdict.details or "Action violates D&D rules."
                        )
                    else:
                        dm_response = verdict.details or "That action is not possible under the current rules."

            # Broadcast response via delivery if configured
            if hasattr(self.session, 'delivery') and self.session.delivery:
                self.session.delivery.master_message(dm_response, tag="DM")
                self.session.delivery.session_updated(self.session)

            return {
                "success": True,
                "dm_response": dm_response,
                "events": [{"event_type": str(getattr(e, 'event_type', e)), "description": getattr(e, 'description', str(e))} for e in events],
                "game_state": {
                    "game_mode": getattr(self.session, 'game_mode', "STORY"),
                    "player_hp": player.character.current_hp,
                    "scene_name": getattr(self.session.scene, 'name', "Unknown") if self.session.scene else "Unknown",
                }
            }

        except CharacterNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[AIGameService] Error processing player action: {e}", exc_info=True)
            raise InvalidActionError(f"Failed to process action: {e}") from e

    async def get_scene_description(self) -> str:
        """
        Get the current scene description using MAGG or the scene object.
        """
        if not self.session or not self.session.scene:
            raise SessionNotInitializedError("Scene is not initialized")

        if hasattr(self.session, 'game_master') and self.session.game_master:
            try:
                return self.session.game_master.get_simple_description()
            except Exception as e:
                logger.warning(f"[AIGameService] Could not generate MAGG scene description: {e}")

        return self.session.scene.description
