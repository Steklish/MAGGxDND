from logging import Logger
from typing import TYPE_CHECKING, List, Optional
if TYPE_CHECKING:
    from game.engine import Session
from game.event_pool import SubscriberQueue
from magg.magg_schemas import SimpleComment, SimpleDescription
from skls_generator.generator import Generator
from schemas.orchestration import Event, Message
from game.manipulators.base_manipulation import Archive


class Magg:
    with open("prompts/DM_personality.md", "r") as f:
        character_prompt = f.read()
    
    def __init__(self, generator : Generator, 
                 archive : Archive | None, 
                 logger : Logger,
                 event_queue : SubscriberQueue) -> None:
        self.generator = generator
        self.archive = archive
        self.logger = logger
        self.event_queue = event_queue
        self.logger.debug("Magg initialized")
        self._session: 'Session | None' = None
    
    @property
    def session(self) -> "Session":
        if self._session is None:
            raise ValueError("Session not injected to Mage!")
        return self._session
    
    def _events_to_string(self, events : List[Event]) -> str:
        events_str = ""
        for e in events:
            events_str += str(e.dict())
        return events_str

    def inject_state(self, state : 'Session') -> None:
        self._session = state
        
    def get_simple_description(self) -> str:
        if self.session is None:
            raise ValueError("Session not injected into Magg")
        
        session_str = self.session.get_session_context()
        prompt = f"""
        {self.character_prompt}
        Generate a vivid description of the current scene in the DND game.
        ## Game state:
        {session_str}
        
        # there is also past conversation history provided with your answers included (use it for natural conversation flow):
        {self.session.get_messages_formatted()}
        """
        description = self.generator.generate_one_shot(
            pydantic_model=SimpleDescription,
            prompt=prompt
        )
        
        new_message = Message(
            sender_name="Mage",
            text=description.description)
        self.session.new_message(new_message)

        return description.description
    
    def comment(self) -> str:
        """Generates a concise comment about recent events in the game."""
        events = self.event_queue.get_all()
        self.event_queue.clear()
        
        session_str = self.session.get_session_context()
        events_str = self._events_to_string(events)
        prompt = f"""
        {self.character_prompt}
        
        Generate a concise comment about the following game events YOU must include all the value changes that took part in events provided. You also must mention everything that is provided in events even if you won't get into much details.  Dont mention 3d coordinates though. Describe events in a way that is engaging and keeps players interested in the game. You are allowed to come up with some flavor and details to make the comment more engaging but you must not contradict the events provided.z
        ## Game state:
        {session_str}
        
        ## Passed events (necessary to mention):
        {events_str}
        
        # there is also past conversation history provided with your answers included (use it for natural conversation flow):
        {self.session.get_messages_formatted()}
        
        those messages are past messages so you dont need to mention them in your comment unless they are relevant to the events provided. Dont repeat yourself. Your messages are seigned as 'Mage'.
        """
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        
        new_message = Message(
            sender_name="Mage",
            text=comment.comment)
        self.session.new_message(new_message)

        return comment.comment
    
    def illegal_action_comment(self, prompt, reasoning, name) -> str:
        prompt = f"""{self.character_prompt} 
        You need to comment on the illegal action attempted by players in a concise manner. (illigal due to {reasoning})
        
        # there is also past conversation history provided with your answers included (use it for natural conversation flow):
        {self.session.get_messages_formatted()}
        """
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        new_message = Message(
            sender_name="Mage",
            text=comment.comment)
        self.session.new_message(new_message)
        return comment.comment
    
    def clarify_user_request(self, correction_question : str) -> str:
        prompt = f"""{self.character_prompt} 
        You need to ask the last playerfor clarification on their request: "{correction_question}". 
        Politely ask for more details so that you can better understand their intentions in the game.
        
        # there is also past conversation history provided with your answers included  (the last user rquest needs clarification to follow game rules more properly):
        {self.session.get_messages_formatted()}
        """
        clarification = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        new_message = Message(
            sender_name="Mage",
            text=clarification.comment)
        self.session.new_message(new_message)
        return clarification.comment