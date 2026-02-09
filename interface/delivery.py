import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from queue import Queue, Empty
from pydantic import BaseModel
from schemas.in_game import Character
if TYPE_CHECKING:
    from entity.player import Player
    from game.engine import Session


class Request(BaseModel):
    """Represents a player request in the queue."""
    player_id: str
    request_text: str
    timestamp: float
    character: Character


class Delivery(ABC):
    """A class that is responsible for interaction with the system. Now handling the cli."""

    def __init__(self):
        self.request_queue: Queue = Queue()
        self._lock = threading.Lock()

    @abstractmethod
    def master_message(self, text : str, tag : str | None = None):
        pass

    @abstractmethod
    def player_request(self, character : Character) -> str:
        """Allows certain player to make a request"""
        pass
    
    @abstractmethod
    def choose_player(self, session : "Session") -> 'Player':
        """Choose which player acts next"""
        pass
    
    
    def put_request(self, request: Request):
        """Add a request to the queue."""
        self.request_queue.put(request)

    def has_requests(self) -> bool:
        """Check if there are any requests in the queue."""
        return not self.request_queue.empty()

    def get_first_request(self) -> Optional[Request]:
        """Fetch the first request in the queue."""
        try:
            # Non-blocking get with timeout to avoid indefinite blocking
            return self.request_queue.get_nowait()
        except Empty:
            return None

    def get_first_request_by_player(self, player_id: str) -> Optional[Request]:
        """Fetch the first request of a certain player."""
        # Since we can't peek into a Queue without removing elements,
        # we'll temporarily store elements and rebuild the queue
        temp_storage = []
        result = None
        
        with self._lock:
            # Drain the queue to find the first request by player
            while not self.request_queue.empty():
                try:
                    req = self.request_queue.get_nowait()
                    temp_storage.append(req)
                    if result is None and req.player_id == player_id:
                        result = req
                        # We found the request, but we still need to store the rest
                except Empty:
                    break
            
            # Put back all requests except the one we found
            for req in temp_storage:
                if req != result:  # Don't put back the one we're returning
                    self.request_queue.put(req)
        
        return result

    def wait_for_request(self, timeout: Optional[float] = None) -> Optional[Request]:
        """Wait for a request to be available in the queue."""
        try:
            # Blocking get with optional timeout
            return self.request_queue.get(timeout=timeout)
        except Empty:
            return None

    def wait_for_request_from_player(self, player_id: str, timeout: Optional[float] = None) -> Optional[Request]:
        """Wait for a request from a specific player."""
        import time

        start_time = time.time()
        # Store requests that don't match the player_id to put back later
        unmatched_requests = []

        while True:
            # Check if we've exceeded the timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                # Put back unmatched requests before returning None
                for req in unmatched_requests:
                    self.request_queue.put(req)
                return None

            # Try to get a request from the queue
            try:
                # Use a small timeout to periodically check if we've exceeded the total timeout
                request_timeout = min(0.1, timeout) if timeout else 0.1
                request = self.request_queue.get(timeout=request_timeout)

                # If this is the request we're looking for, return it
                if request.player_id == player_id:
                    # Put back all unmatched requests
                    for req in unmatched_requests:
                        self.request_queue.put(req)
                    return request
                else:
                    # Store unmatched request to put back later
                    unmatched_requests.append(request)

            except Empty:
                # Continue the loop if nothing was retrieved within the timeout
                continue

    def draw_ascii_scene(self, session):
        """Draw an ASCII representation of the current scene with characters and objects."""
        if not session.current_scene:
            print("\n[No current scene loaded]")
            return

        print("\n" + "="*60)
        print(f"📍 {session.current_scene.name.upper()}")
        print("="*60)
        self._print_turn_queue(session)

        # Get scene dimensions and center
        center_x, center_y = (session.current_scene.center_position.x,
                              session.current_scene.center_position.y)
        width = session.current_scene.dimensions.x
        height = session.current_scene.dimensions.y

        # Calculate boundaries
        min_x = center_x - width/2
        max_x = center_x + width/2
        min_y = center_y - height/2
        max_y = center_y + height/2

        print(f"📏 Scene: {width}x{height} {session.current_scene.scale_unit} | Center: ({center_x}, {center_y})")
        print(f"💬 {session.current_scene.description}")

        # Create a 2D grid representation
        # We'll use a simple grid where each cell represents a 1-unit area
        grid_size = 20  # Fixed grid size for visualization
        grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]

        # Calculate scaling factors to map scene coordinates to grid positions
        x_scale = grid_size / width if width > 0 else 1
        y_scale = grid_size / height if height > 0 else 1

        # Place characters on the grid
        for player in session.players:
            char = player.character
            if hasattr(char, 'position') and char.position:
                # Map position to grid coordinates
                grid_x = int((char.position.x - min_x) * x_scale)
                grid_y = int((char.position.y - min_y) * y_scale)

                # Keep within bounds
                grid_x = max(0, min(grid_size - 1, grid_x))
                grid_y = max(0, min(grid_size - 1, grid_y))

                # Use first letter of name or 'P' for player
                symbol = char.name[0].upper() if char.name else 'P'
                grid[grid_y][grid_x] = f'\033[34m{symbol}\033[0m'  # Blue for players

        # Place NPCs on the grid
        for npc in session.npcs:
            npc_char = npc.character
            if npc_char.current_scene == session.current_location_name:  # Only show NPCs in current scene
                if hasattr(npc_char, 'position') and npc_char.position:
                    # Map position to grid coordinates
                    grid_x = int((npc_char.position.x - min_x) * x_scale)
                    grid_y = int((npc_char.position.y - min_y) * y_scale)

                    # Keep within bounds
                    grid_x = max(0, min(grid_size - 1, grid_x))
                    grid_y = max(0, min(grid_size - 1, grid_y))

                    # Use first letter of name or 'N' for NPC
                    symbol = npc_char.name[0].upper() if npc_char.name else 'N'
                    grid[grid_y][grid_x] = f'\033[31m{symbol}\033[0m'  # Red for NPCs

        # Place objects on the grid
        for obj in session.current_scene.objects:
            if hasattr(obj, 'position') and obj.position:
                # Map position to grid coordinates
                grid_x = int((obj.position.x - min_x) * x_scale)
                grid_y = int((obj.position.y - min_y) * y_scale)

                # Keep within bounds
                grid_x = max(0, min(grid_size - 1, grid_x))
                grid_y = max(0, min(grid_size - 1, grid_y))

                # Use first letter of object name or 'O' for object
                symbol = obj.name[0].upper() if obj.name else 'O'
                grid[grid_y][grid_x] = f'\033[33m{symbol}\033[0m'  # Yellow for objects

        # Print the grid
        print("\n🗺️  SCENE MAP:")
        for row in grid:
            print(' '.join(row))

        # Print legend
        print("\n📋 LEGEND:")
        print(f"  \033[34mP\033[0m - Players ({', '.join([p.character.name for p in session.players])})")
        print(f"  \033[31mN\033[0m - NPCs ({', '.join([n.character.name for n in session.npcs if n.character.current_scene == session.current_location_name])})")
        print(f"  \033[33mO\033[0m - Objects ({', '.join([o.name for o in session.current_scene.objects])})")
        print(f"  \033[32m.\033[0m - Empty space")

        # Print character statuses
        print("\n👤 CHARACTER STATUS:")
        for player in session.players:
            char = player.character
            status = f"  🧍 {char.name}: HP {char.current_hp}/{char.max_hp}, Pos ({char.position.x}, {char.position.y})"
            if char.active_conditions and char.active_conditions.strip():
                # active_conditions is a string with newlines, split by newline to get individual conditions
                conditions = [cond.strip() for cond in char.active_conditions.split('\n') if cond.strip()]
                if conditions:
                    status += f" ⚠️  {', '.join(conditions)}"
            print(status)

        for npc in session.npcs:
            npc_char = npc.character
            if npc_char.current_scene == session.current_location_name:
                status = f"  👹 {npc_char.name}: HP {npc_char.current_hp}/{npc_char.max_hp}, Pos ({npc_char.position.x}, {npc_char.position.y})"
                if npc_char.active_conditions and npc_char.active_conditions.strip():
                    # active_conditions is a string with newlines, split by newline to get individual conditions
                    conditions = [cond.strip() for cond in npc_char.active_conditions.split('\n') if cond.strip()]
                    if conditions:
                        status += f" ⚠️  {', '.join(conditions)}"
                print(status)

        print("="*60)

    def _print_turn_queue(self, session):
        """Print a beautiful and informative representation of the turn queue."""
        if not session.turn_queue:
            print("🕐 Turn Queue: Empty")
            return

        print("🕐 TURN QUEUE:")
        print("┌─────────────────────────────────────────────────────────┐")

        # Sort the queue by turn time to show the order
        sorted_queue = sorted(session.turn_queue, key=lambda x: x[2])

        for i, (char, time_added, next_turn) in enumerate(sorted_queue):
            # Determine character name and type
            if hasattr(char, 'character'):
                name = char.character.name # type: ignore
                char_type = "👤" if hasattr(char, '_init_player') or 'Player' in str(type(char)) else "👹"
            else:
                name = "Round Determinator"
                char_type = "🔄"

            # Format the turn time
            turn_time_str = f"{next_turn:.2f}"

            # Determine if this is the next to act
            is_next = i == 0

            # Create the entry with appropriate highlighting
            if is_next:
                print(f"│ 🎯 NEXT: {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")
            else:
                print(f"│        {char_type} {name:<20} │ Turn: {turn_time_str:>6} │")

        print("└─────────────────────────────────────────────────────────┘")
        print(f"⏱️  Global Time: {session.turn_time:.2f}")
    
    