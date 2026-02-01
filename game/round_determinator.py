from logging import Logger
from typing import TYPE_CHECKING
from schemas.orchestration import Event, EventTypes
from schemas.in_game import Character, GameModes

if TYPE_CHECKING:
    from game.engine import Session


class RoundDeterminator:
    """Special object that analyzes game state and determines if mode changes are needed."""
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self._session: 'Session | None' = None

    @property
    def session(self) -> "Session":
        if self._session is None:
            raise ValueError("Session not injected to RoundDeterminator!")
        return self._session

    def inject_state(self, state: 'Session') -> None:
        self._session = state

    def run(self) -> list[Event]:
        """Analyze game state and determine if mode changes are needed."""
        self.logger.debug("RoundDeterminator analyzing game state...")

        # First, clean up expired conditions
        condition_cleanup_events = self._cleanup_expired_conditions()

        # Analyze recent events to determine appropriate game mode
        current_mode = self.session.game_mode
        suggested_mode = self._analyze_game_state()

        # If mode needs to change, generate a mode change event
        if current_mode != suggested_mode:
            self.logger.info(f"RoundDeterminator suggesting mode change from {current_mode.value} to {suggested_mode.value}")

            mode_change_event = Event(
                event_type=EventTypes.LOCATION_STATUS_CHANGE,  # Using a generic event type for mode change
                event_initiator="System",
                event_subject="GameMode",
                description=f"Mode change from {current_mode.value} to {suggested_mode.value}",
            ) # type: ignore

            # Update the session's game mode
            self.session.game_mode = suggested_mode

            return condition_cleanup_events + [mode_change_event]

        self.logger.debug("RoundDeterminator: No mode change needed")
        return condition_cleanup_events

    def _cleanup_expired_conditions(self) -> list[Event]:
        """Check all characters and remove expired conditions."""
        events = []

        # Get all characters in the session
        all_characters = self.session.get_all_characters()

        for character in all_characters:
            # Check each condition to see if it should expire
            conditions_to_remove = []

            for condition in character.active_conditions:
                # Define conditions that should expire after a certain period
                # For now, we'll implement a simple system where some conditions expire automatically
                if self._should_condition_expire(condition, character):
                    conditions_to_remove.append(condition)

            # Remove expired conditions and generate events
            for condition in conditions_to_remove:
                character.active_conditions.remove(condition)

                # Create an event for the condition removal
                event = Event(
                    event_type=EventTypes.CHARACTER_STATUS_CHANGE,
                    event_initiator="System",
                    event_subject=character.name,
                    event_target="active_conditions",
                    description=f"Removed expired condition '{condition}' from {character.name}"
                )
                events.append(event)

                self.logger.info(f"Removed expired condition '{condition}' from {character.name}")

        return events

    def _should_condition_expire(self, condition: str, character: 'Character') -> bool:
        """Determine if a condition should expire."""
        # Define conditions that should expire automatically
        temporary_conditions = [
            "Concentration",
            "Rage",
            "Reckless Attack",
            "Advantage",
            "Disadvantage",
            "Invisible",
            "Poisoned",
            "Stunned",
            "Prone",
            "Restrained",
            "Frightened",
            "Charmed",
            "Paralyzed",
            "Grappled"
        ]

        # For now, we'll assume all temporary conditions expire after one "round"
        # In a more complex system, you might track duration or implement more sophisticated logic
        return condition in temporary_conditions

    def _analyze_game_state(self):
        """Analyze the current game state to determine the appropriate mode."""
        # Get all events from the event pool and clear them
        all_events = self.session.event_pool.get_events()
        self.session.event_pool.clear_events()  # Clear the pool after fetching

        # If no events, maintain current mode
        if not all_events:
            return self.session.game_mode

        # More precise scoring system for combat vs story events
        combat_score = 0
        story_score = 0

        for event in all_events:
            # Base scoring by event type
            if event.event_type in [EventTypes.CHARACTER_STATS_UPDATE, EventTypes.CHARACTER_DEATH, EventTypes.CHARACTER_STATUS_CHANGE]:
                # These are typically combat-related events
                base_score = 2  # Higher weight for combat events

                # Boost score if combat-related terms are present
                desc_lower = event.description.lower()
                combat_terms = ["damage", "attack", "hit", "kill", "fight", "combat", "hp", "strength", "defend", "strike", "weapon"]
                term_bonus = sum(2 for term in combat_terms if term in desc_lower)

                combat_score += base_score + term_bonus
            elif event.event_type in [EventTypes.SCENE_UPDATE, EventTypes.CHARACTER_TRANSFER, EventTypes.NPC_TRANSFER]:
                # These are typically story-related events
                base_score = 2  # Higher weight for story events

                # Boost score if story-related terms are present
                desc_lower = event.description.lower()
                story_terms = ["explore", "discover", "talk", "dialogue", "investigate", "look", "examine", "approach", "enter", "leave", "travel"]
                term_bonus = sum(2 for term in story_terms if term in desc_lower)

                story_score += base_score + term_bonus
            else:
                # Other events get lower base weight but still contribute
                base_score = 1

                # Determine context based on description
                desc_lower = event.description.lower()

                # Check for combat indicators
                combat_terms = ["damage", "attack", "hit", "kill", "fight", "combat", "hp", "strength", "defend", "strike", "weapon"]
                if any(term in desc_lower for term in combat_terms):
                    combat_score += base_score
                else:
                    # Default to story for other events
                    story_score += base_score

        # Determine mode based on scores
        total_score = combat_score + story_score
        if total_score == 0:
            # If no score, maintain current mode
            return self.session.game_mode

        combat_ratio = combat_score / total_score
        story_ratio = story_score / total_score

        # More nuanced thresholds for mode determination
        if combat_ratio >= 0.35:  # At least 35% combat scoring
            return GameModes.COMBAT
        elif story_ratio >= 0.35:  # At least 35% story scoring
            return GameModes.STORY
        else:
            # If neither clearly dominates, maintain current mode
            return self.session.game_mode