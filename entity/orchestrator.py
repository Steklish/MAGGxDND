from logging import Logger
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from game.engine import Session
    from entity.npc import NPC
    from entity.player import Player
from skls_generator.generator import Generator
from schemas.orchestration import OrchestrationVerdict, OrchestrationVerdictType, RuleViolationObject, RulesCheck, UserInteractionProcessing, UserInterationType, ClarityCheck
from game.manipulators.base_manipulation import Archive, BaseManipulation

MAX_MESSAGES_HISTORY_PROVIDED = 6
MAX_EVENTS_PROVIDED = 5

class Orchestrator:
    """Class that handles input from users and passes it to a appropriate handler"""
    def __init__(self, generator : Generator, logger : Logger) -> None:
        self.generator = generator
        self.manipulations : List[BaseManipulation] = []
        self.logger = logger
        
        with open("prompts/character_action_rules.md", "r") as f:
            self.character_action_rules = f.read()

        with open("prompts/combat.md", "r") as f:
            self.combat_rules = f.read()
        with open("prompts/story.md", "r") as f:
            self.story_rules = f.read()
        
    def add_state(self, state : "Session"):
        self.state = state
        
    def request(self, username : str, request_text : str, message_cahce : str | None = None) -> UserInteractionProcessing:
        if not self.state:
            raise ValueError("Orchestrator has no state assigned.")
        m_history = ""
        for m in self.state.messages[0:MAX_MESSAGES_HISTORY_PROVIDED]:
            m_history += f"\n\n sender: {m.sender_name}\n text: {m.text}"


        prompt = f"""
        You need to decide what is user interaction based on the game state and message history.

        ## User Request:
        {request_text}

        ## Messages history (meta game):
        {m_history}

        ## Game state:
        {self.state.get_session_context()}

        ## Classification Instructions:
        - CHARACTER_ACTION: When the user wants their character to perform an in-game action (attack, move, cast a specific spell, interact with objects, etc.)
        - META_COMMENT: When the user is asking for information about their character (spells, abilities, inventory, stats), asking for clarification about the game, or making meta-game observations

        Determine if this is a CHARACTER_ACTION or META_COMMENT, and enhance the user's request with all available context.
        {f'\nThere is precious clarifications and meta comments history provided: {message_cahce}' if message_cahce else ''}
        """
        return self.generator.generate_one_shot(
            pydantic_model=UserInteractionProcessing,
            prompt=prompt
        )
        
        
    def meta_interaction(self, username : str, request_text : str):
        pass


    def character_action_story(self, character : 'Player | NPC', request_text : str, processed_interaction : UserInteractionProcessing) -> OrchestrationVerdict:
        # First check if the action needs clarification
        clarity_check = self._check_action_clarity(character, request_text, processed_interaction)
        if clarity_check.needs_clarification:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.CLAIRIFICATION_NEEDED,
                details=clarity_check.clarification_needed,
                original_request=request_text
            )

        # Then check if the action violates rules
        check_object = self._check_against_the_rules(character, request_text, processed_interaction)
        if check_object is not None:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION,
                details=check_object.details,
                original_request=request_text
            )
        else:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.ALLOWED_PLAYER_ACTION,
                details=request_text,
                original_request=request_text
            )
        
    def character_action_combat(self, character : 'Player | NPC', request_text : str, processed_interaction : UserInteractionProcessing) -> OrchestrationVerdict:
        # First check if the action needs clarification
        clarity_check = self._check_action_clarity(character, request_text, processed_interaction)
        if clarity_check.needs_clarification:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.CLAIRIFICATION_NEEDED,
                details=clarity_check.clarification_needed,
                original_request=request_text
            )

        # Then check if the action violates rules
        check_object = self._check_rules_combat(character, request_text, processed_interaction)
        if check_object is not None:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION,
                details=check_object.details,
                original_request=request_text
            )
        else:
            return OrchestrationVerdict(
                verdict_type=OrchestrationVerdictType.ALLOWED_PLAYER_ACTION,
                details=request_text,
                original_request=request_text
            )
    
    def _check_against_the_rules(self, character : 'Player | NPC', request_text : str, processed_interaction : UserInteractionProcessing) -> RuleViolationObject | None:
        """Iterates if clarification is needed. (IN COMBAT MODE)"""
        if self.state.game_mode == "COMBAT":
            return self._check_rules_combat(character, request_text, processed_interaction)
        else:
            return self._check_rules_story(character.character.name, request_text, processed_interaction)
    
    def _check_rules_combat(self, character : 'Player | NPC', request_text : str, processed_interaction : UserInteractionProcessing) -> RuleViolationObject | None:
        """Iterates if clarification is needed."""

        # Get recent messages for context
        m_history = ""
        for m in self.state.messages[-MAX_MESSAGES_HISTORY_PROVIDED:]:
            m_history += f"\n\n sender: {m.sender_name}\n text: {m.text}"

        check = self.generator.generate_one_shot(
            pydantic_model=RulesCheck,
            prompt=self.combat_rules + f"\n\nRecent Messages History:\n{m_history}\n\n{character.character.name} requests {request_text} \n\n User interaction: {processed_interaction.user_request_saturated}\n\n Does this interaction violate any combat dnd rules?"
        )
        if check.is_rule_violation:
            return RuleViolationObject(details=check.violation_details if check.violation_details else "No details provided")
        else:
            return None
    
    def _check_rules_story(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing) -> RuleViolationObject | None:

        # Get recent messages for context
        m_history = ""
        for m in self.state.messages[-MAX_MESSAGES_HISTORY_PROVIDED:]:
            m_history += f"\n\n sender: {m.sender_name}\n text: {m.text}"

        check = self.generator.generate_one_shot(
            pydantic_model=RulesCheck,
            prompt=self.story_rules + f"\n\nRecent Messages History:\n{m_history}\n\n{username} requests {request_text} \n\n User interaction: {processed_interaction.user_request_saturated}\n\n Does this interaction violate any story rules? Answer in JSON format."
        )
        if check.is_rule_violation:
            return RuleViolationObject(details=check.violation_details if check.violation_details else "No details provided")
        else:
            return None

    def _check_action_clarity(self, character: 'Player | NPC', request_text: str, processed_interaction: UserInteractionProcessing) -> 'ClarityCheck':
        """Check if the action needs clarification before checking if it violates rules."""

        # Get recent messages for context
        m_history = ""
        for m in self.state.messages[-MAX_MESSAGES_HISTORY_PROVIDED:]:
            m_history += f"\n\n sender: {m.sender_name}\n text: {m.text}"

        clarity_prompt = f"""
        You are reviewing a player action to determine if it needs clarification before being processed.

        ## Action Request:
        {request_text}

        ## Processed Interaction:
        {processed_interaction.user_request_saturated}

        ## Recent Messages History (meta game):
        {m_history}

        ## Character Information:
        Name: {character.character.name}
        Current Position: ({character.character.position.x}, {character.character.position.y})

        ## Current Game State:
        {self.state.get_session_context()}

        Determine if this action is clear enough to be processed, or if it needs additional clarification.
        For example, if the player says "I cast a spell" without specifying which spell, or "I move" without specifying direction/distance,
        these would need clarification. If it is obvious what player is have in mind you dont need to clarify it. If there is unsignificant detail misiing you shuoldn't request clarification. Request clarification if vital details are missing.

        Consider the recent message history to understand the context of the current request.
        For instance, if the player was asking about their spells in previous messages, this might be a continuation of that inquiry.

        Respond with whether clarification is needed and what specifically needs clarification.
        """

        clarity_result = self.generator.generate_one_shot(
            pydantic_model=ClarityCheck,
            prompt=clarity_prompt
        )

        return clarity_result