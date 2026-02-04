from interface.delivery import Delivery
from schemas.in_game import Character


class TerminalDelivery(Delivery):
    """A class that is responsible for interaction with the system. Now handling the cli."""
    
    def master_message(self, text : str, tag : str | None = None):
        print(f"\033[31mDM {tag if tag else ''}: {text}\033[0m")
        
    def player_request(self, character : Character):
        prompt = (
            f"\033[35mPlayer {character.name}, enter your action "
            f"(current position: ({character.position.x}, "
            f"{character.position.y})): \033[0m"
        )
        return input(prompt)