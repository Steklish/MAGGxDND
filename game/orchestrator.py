from logging import Logger
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from game.engine import Session
    from npcs.npc import NPC
    from player.player import Player
from skls_generator.generator import Generator
from schemas.orchestration import OrchestrationVerdict, OrchestrationVerdictType, RuleViolationObject, RulesCheck, UserInteractionProcessing, UserInterationType
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
        
    def request(self, username : str, request_text : str) -> UserInteractionProcessing:
        if not self.state:
            raise ValueError("Orchestrator has no state assigned.")
        m_history = ""
        for m in self.state.messages[0:MAX_MESSAGES_HISTORY_PROVIDED]:  
            m_history += f"\n\n sender: {m.sender_name}\n text: {m.text}"
   
        
        prompt = f"""
        You need to decide what is user interaction based on the game state and message history.
        ## Messages history (meta game):
        {m_history}
        
        ## Game state:
        {self.state.get_session_context()}
        """
        return self.generator.generate_one_shot(
            pydantic_model=UserInteractionProcessing,
            prompt=prompt
        )
        
        
    def meta_interaction(self, username : str, request_text : str):
        pass


    def character_action_story(self, character : 'Player | NPC', request_text : str, processed_interaction : UserInteractionProcessing) -> OrchestrationVerdict:
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
        check = self.generator.generate_one_shot(
            pydantic_model=RulesCheck,
            prompt=self.combat_rules + f"{character.character.name} requests {request_text} \n\n User interaction: {processed_interaction.user_request_saturated}\n\n Does this interaction violate any combat dnd rules?"
        )
        if check.is_rule_violation:
            return RuleViolationObject(details=check.violation_details if check.violation_details else "No details provided")
        else:
            return None
    
    def _check_rules_story(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing) -> RuleViolationObject | None:
        check = self.generator.generate_one_shot(
            pydantic_model=RulesCheck,
            prompt=self.story_rules + f"{username} requests {request_text} \n\n User interaction: {processed_interaction.user_request_saturated}\n\n Does this interaction violate any story rules? Answer in JSON format."
        )
        if check.is_rule_violation:
            return RuleViolationObject(details=check.violation_details if check.violation_details else "No details provided")
        else:
            return None