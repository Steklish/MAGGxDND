from logging import Logger
from typing import List
from game.engine import Session
from skls_generator.generator import Generator
from schemas.orchestration import Event, StoryRulesCheck, UserInteractionProcessing, UserInterationType
from game.manipulators.base_manipulation import Archive, BaseManipulation

MAX_MESSAGES_HISTORY_PROVIDED = 6
MAX_EVENTS_PROVIDED = 5

class Orchestrator:
    """Class that handles input from users and passes it to a appropriate handler"""
    def __init__(self, generator : Generator, state : Session, logger : Logger) -> None:
        self.generator = generator
        self.manipulations : List[BaseManipulation] = []
        self.state = state
        self.logger = logger
        
        with open("/prompts/character_action_rules.md", "r") as f:
            self.character_action_rules = f.read()
            
        with open("/prompts/combat.md", "r") as f:
            self.combat_rules = f.read()
        with open("/prompts/story.md", "r") as f:
            self.story_rules = f.read()
        
        
        
    def request(self, username : str, request_text : str):
        
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
        self.generator.generate_one_shot(
            pydantic_model=UserInteractionProcessing,
            prompt=prompt
        )
        
        
    def meta_interaction(self, username : str, request_text : str):
        pass

    def character_action(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing):
        pass    
    
    def _check_against_the_rules(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing):
        if self.state.game_mode == "COMBAT":
            self._check_rules_combat(username, request_text, processed_interaction)
        else:
            self._check_rules_story(username, request_text, processed_interaction)
    
    def _check_rules_combat(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing):
        pass
    
    def _check_rules_story(self, username : str, request_text : str, processed_interaction : UserInteractionProcessing):
        self.generator.generate_one_shot(
            pydantic_model=StoryRulesCheck,
            prompt=self.story_rules + f"{username} requests {request_text} \n\n User interaction: {processed_interaction.user_request_saturated}\n\n Does this interaction violate any story rules? Answer in JSON format."
        )
        
        pass
    