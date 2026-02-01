from logging import Logger
from typing import TYPE_CHECKING

from schemas.orchestration import Event, Message, OrchestrationVerdictType, UserInterationType
if TYPE_CHECKING:
    from game.engine import Session
from game.orchestrator import Orchestrator
from schemas.in_game import Character, GameModes
from game.game_entity import GameEntity
from game.manipulators.attack_manipulation import AttackManipulation
from game.manipulators.character_movement_manipulation import CharacterMovementManipulation


class Player(GameEntity):
    def __init__(self, character: Character,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 session: 'Session',
                 ) -> None:
        super().__init__(session=session)
        self.character = character
        self._player_logger = logger  # Store the logger separately to avoid conflict
        self.orchestrator = orchestrator
        
        # Initialize default manipulators
        self.attack_manipulator = AttackManipulation(generator=None, logger=self._player_logger, session=self.session)
        self.movement_manipulator = CharacterMovementManipulation(generator=None, logger=self._player_logger, session=self.session)
        self.manipulators = [self.attack_manipulator, self.movement_manipulator]

        # Update manipulators based on inventory/spells
        self._update_manipulators()

    def request_terminal_input(self) -> str:
        # Prepare the prompt with proper encoding handling
        prompt = (
            f"\033[35mPlayer {self.character.name}, enter your action "
            f"(current position: ({self.character.position.x}, "
            f"{self.character.position.y})): \033[0m"
        )
        return input(prompt)

    def run(self) -> list[Event]:
        """Player's turn. Returns a list of events based on player action.
        Handles three possible outcomes: legal action, unclear action needing clarification,
        and illegal action requiring a new one."""

        while True:
            self._player_logger.debug(f"Waiting for player input for {self.character.name}")

            request = self.request_terminal_input()

            if request.strip() == "":
                # Skip turn - return empty list of events
                return []

            new_message = Message(
                sender_name=self.character.name,
                text=request)
            self.session.new_message(new_message)

            user_interaction = self.orchestrator.request(
                username=self.character.name,
                request_text=request
            )

            if user_interaction.interaction_type == UserInterationType.CHARACTER_ACTION:
                if self.session.game_mode == GameModes.COMBAT:
                    verdict = self.orchestrator.character_action_combat(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )
                else:
                    verdict = self.orchestrator.character_action_story(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )

                # Handle the three possible outcomes
                if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    # Legal action - proceed to generate events using entity manipulator
                    description = verdict.details if verdict.details else request

                    # Generate intent events from description using global manipulator as event generator
                    intent_events = self.session.manipulator.external_action(description, actor=self.character.name)

                    # Process intent events using entity manipulators
                    results = []
                    for event in intent_events:
                        event_results = self.manage_event(event)
                        if event_results:
                            results.extend(event_results)
                        else:
                            # If entity doesn't have a manipulator for this event, it might be a global event
                            results.append(event)

                    return results
                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Unclear action - need clarification from user
                    # Send clarification request to game master
                    clarification_response = self.session.game_master.clarify_user_request(
                        correction_question=verdict.details if verdict.details else "Action needs clarification"
                    )
                    print(f"\033[31mDM Clarification: {clarification_response}\033[0m")
                    # Continue the loop to get a new action
                    continue
                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    # Illegal action - request a new one
                    illegal_response = self.session.game_master.illegal_action_comment(
                        prompt=request,
                        name=self.character.name,
                        reasoning=verdict.details if verdict.details else "Action is not allowed"
                    )
                    print(f"\033[31mDM Illegal Action: {illegal_response}\033[0m")
                    # Continue the loop to get a new action
                    continue
            elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta comment - this is a direct question/query to the game master
                # Process it and continue the loop to get an actual action
                meta_response = self.session.game_master.comment_on_meta_request(request)
                print(f"\033[31mDM Meta Response: {meta_response}\033[0m")
                # Continue the loop to get a real action from the player
                continue

            # Default case - return empty list
            return []
