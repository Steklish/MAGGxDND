from logging import Logger
from typing import TYPE_CHECKING, Tuple
from core.game.event_pool import SubscriberQueue
from core.interface.delivery import Delivery
from core.utils.colors import Colors
if TYPE_CHECKING:
    from core.game.engine import Session
    from core.entity.player import Player
    from core.schemas.in_game import Character

class NativeTerminalDelivery(Delivery):
    """
    A class that handles delivery using native terminal input/output.
    """

    def __init__(self, event_queuee : SubscriberQueue, logger : Logger):
        super().__init__(event_queuee, logger)  # Initialize parent class (with queue)

    def master_message(self, text: str, tag: str | None = None):
        """Display a message from the game master (DM)."""
        formatted_text = Colors.colorize(
            text=f"DM {tag if tag else ''}: {text}",
            color_code=Colors.BG_YELLOW + Colors.BLACK)
        print(formatted_text)

    def session_updated(self, session : "Session") -> None:
        """Used as a callback when a session is being updated to sent to the delivey instance."""
        ...
    
    def player_request(self, character: 'Character') -> str:
        """Get input from a specific player."""
        # First, check if there's already a request for this player in the queue
        # We'll temporarily store requests to find the one for this player
        temp_storage = []
        target_request = None
        
        with self._lock:
            # Drain the queue to find the first request by player
            while not self.request_queue.empty():
                try:
                    req = self.request_queue.get_nowait()
                    if target_request is None and req.player_id == character.name:
                        target_request = req  # Found the request for this player
                    else:
                        temp_storage.append(req)  # Store other requests to add back later
                except:
                    break
            
            # Put back all requests except the one we found for this player
            for req in temp_storage:
                self.request_queue.put(req)
        
        if target_request:
            # If there's a request for this player, return its text
            return target_request.request_text or ""
        else:
            # No existing request for this player, get input from terminal
            prompt = (
                f"Player {character.name}, enter your action "
                f"(current position: ({character.position.x}, "
                f"{character.position.y})): "
            )
            prompt = Colors.colorize(prompt, Colors.BRIGHT_MAGENTA)
            print(prompt, end="")
            user_input = input()
            return user_input

    def any_player_request(self, session: "Session") -> Tuple[str, 'Character']:
        """Get input from any player - first ask for character name, then the action."""
        # Wait for any request to be available in the queue
        request = self.wait_for_request()
        if request:
            # Return the request text and character from the queued request
            return request.request_text, request.character
        else:
            # If no request is queued, get input from terminal
            # First ask which character is taking the action
            while True:  # Keep asking until a valid character is found
                print(Colors.colorize("Available characters:", Colors.BRIGHT_YELLOW))
                for player in session.players:
                    print(Colors.colorize(f"- {player.character.name}", Colors.BRIGHT_GREEN))
                
                char_name = input(Colors.colorize("Which character is acting? ", Colors.BRIGHT_YELLOW))
                
                # Find the character in the session
                player_entity = session.find_entity_by_name(char_name)
                if player_entity and hasattr(player_entity, 'character'):
                    character = player_entity.character
                    break  # Exit the loop when a valid character is found
                else:
                    print(Colors.colorize(f"Character '{char_name}' not found. Please try again.", Colors.BRIGHT_RED))
            
            # Now get the action
            prompt = (
                f"Player {character.name}, enter your action "
                f"(current position: ({character.position.x}, "
                f"{character.position.y})): "
            )
            prompt = Colors.colorize(prompt, Colors.BRIGHT_MAGENTA)
            print(prompt, end="")
            user_input = input()
            
            return user_input, character

    def choose_player(self, session: "Session") -> "Player":
        """Choose which player acts next. This step is blocks the game loop btw"""
        # Display available players and let the user choose
        print(Colors.colorize("Choose which player acts next:", Colors.BRIGHT_YELLOW))
        for i, player in enumerate(session.players, 1):
            print(Colors.colorize(f"{i}. {player.character.name}", Colors.BRIGHT_GREEN))
        
        while True:
            try:
                choice = input(Colors.colorize("Enter the number of the player to act: ", Colors.BRIGHT_YELLOW))
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(session.players):
                    return session.players[choice_idx]
                else:
                    print(Colors.colorize("Invalid choice. Please select a valid player number.", Colors.BRIGHT_RED))
            except ValueError:
                print(Colors.colorize("Invalid input. Please enter a number.", Colors.BRIGHT_RED))