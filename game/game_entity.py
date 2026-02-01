from typing import List, Optional, TYPE_CHECKING, Any
if TYPE_CHECKING:
    from game.engine import Session
from schemas.orchestration import Event

class GameEntity:
    def __init__(self, session: 'Session'):
        self.manipulators = []
        self._session = session # Make session protected
        self.inventory = []
        self.spells = []

    @property
    def session(self):
        return self._session

    @property
    def generator(self):
        return self._session.generator

    @property
    def logger(self):
        return self._session.logger

    @property
    def players(self):
        return self._session.players
    
    @property
    def npcs(self):
        return self._session.npcs

    def add_manipulator(self, manipulator):
        self.manipulators.append(manipulator)

    def remove_manipulator(self, manipulator):
        self.manipulators.remove(manipulator)

    def add_item(self, item):
        self.inventory.append(item)
        self._update_manipulators()

    def remove_item(self, item):
        self.inventory.remove(item)
        self._update_manipulators()

    def add_spell(self, spell):
        self.spells.append(spell)
        self._update_manipulators()

    def remove_spell(self, spell):
        self.spells.remove(spell)
        self._update_manipulators()

    def _update_manipulators(self):
        # Remove all existing manipulators except the default ones
        # Use class names for comparison
        default_class_names = ['AttackManipulation', 'CharacterMovementManipulation']
        self.manipulators = [m for m in self.manipulators if m.__class__.__name__ in default_class_names]

        # Collect all desired manipulator names from inventory and spells
        desired_manipulators = set()
        for item in self.inventory:
            for m_name in getattr(item, 'available_manipulators', []):
                desired_manipulators.add(m_name)
        for spell in self.spells:
            for m_name in getattr(spell, 'available_manipulators', []):
                desired_manipulators.add(m_name)

        # Add manipulators
        for manipulator_name in desired_manipulators:
            # Skip if already added
            if any(m.__class__.__name__ == manipulator_name for m in self.manipulators):
                continue
                
            try:
                # Find the module containing the manipulator
                import importlib
                import pkgutil
                import game.manipulators
                
                manipulator_class = None
                for loader, module_name, is_pkg in pkgutil.walk_packages(game.manipulators.__path__, game.manipulators.__name__ + '.'):
                    module = importlib.import_module(module_name)
                    if hasattr(module, manipulator_name):
                        manipulator_class = getattr(module, manipulator_name)
                        break
                
                if manipulator_class:
                    manipulator = manipulator_class(generator=self.generator, logger=self.logger, session=self._session)
                    self.add_manipulator(manipulator)
                    self.logger.debug(f"Dynamically added manipulator {manipulator_name} to {self.character.name if hasattr(self, 'character') else 'entity'}")
                else:
                    self.logger.warning(f"Manipulator {manipulator_name} not found in game.manipulators package.")
            except Exception as e:
                self.logger.error(f"Error dynamically loading manipulator {manipulator_name}: {e}")

    def manage_event(self, event: Event) -> List[Event]:
        """Process an event using the entity's manipulators."""
        for manipulator in self.manipulators:
            if event.event_type in manipulator.event_types_binded:
                # Check if it's an entity-specific manipulator (taking 2 args) or global (taking 1)
                # Actually, all entity manipulators should now take (character, event)
                # Global manipulators (if any were added to entity) might take (event)
                try:
                    # Try calling with character context
                    return manipulator.manipulate(self.character, event)
                except TypeError:
                    # Fallback to single argument if it doesn't accept character
                    return manipulator.manipulate(event)
        return []

    def move_character_to_position(self, character, target_pos):
        """Move character to a new position within the scene."""
        # Check if the target position is within scene bounds
        if character.current_scene:
            scene = self._session.get_scene(character.current_scene)
            if scene:
                if target_pos.x < 0 or target_pos.x > scene.dimensions.x or \
                        target_pos.y < 0 or target_pos.y > scene.dimensions.y:
                    print(f"Target position ({target_pos.x}, {target_pos.y}) is out of scene bounds.")
                    return False

                # Update character position
                character.position = target_pos
                print(f"Character {character.name} moved to ({target_pos.x}, {target_pos.y}).")
                return True
            else:
                print(f"Scene {character.current_scene} not found.")
                return False
        else:
            print("Character is not in any scene.")
            return False
