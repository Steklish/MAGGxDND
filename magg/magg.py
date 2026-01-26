from logging import Logger
from typing import List
from game.event_pool import SubscriberQueue
from magg.magg_schemas import SimpleComment
from skls_generator.generator import Generator
from schemas.orchestration import Event
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
        
    def _events_to_string(self, events : List[Event]) -> str:
        events_str = ""
        for e in events:
            events_str += str(e.dict())
        return events_str
        
    def comment(self, state : str) -> str:
        events = self.event_queue.get_all()
        self.event_queue.clear()
        events_str = self._events_to_string(events)
        prompt = f"""
        {self.character_prompt}
        Generate a concise comment about the following game events
        ## Game state:
        {state}
        
        ## Passed events:
        {events_str}
        """
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        return comment.comment