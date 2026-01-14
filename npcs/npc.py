from schemas.in_game import Character, NPCCharacter


class NPC:
    """The idea is that the NPC class creature is intependent actor 
    (independent from game master/ narrator) but the narrator 
    will describe its actions. 
    It listens to the events and decides if to act or not.
    
    If an NPC acts after an event, it will generate a new event.
    
    Multiple events can be processed at a time.
    """
    
    def __init__(self, character : NPCCharacter) -> None:
        self.character = character
        
        
    def handle_events(self, events: list[str]):
        """Process a list of events and decide on an action.
        
        Args:
            events (list[str]): A list of event descriptions."""
            
        pass