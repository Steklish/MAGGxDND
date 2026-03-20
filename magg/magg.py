import os
from logging import Logger
from typing import TYPE_CHECKING, List, Optional

from utils.threads import run_list_in_parallel, run_list_in_parallel_generator
if TYPE_CHECKING:
    from game.engine import Session
from game.event_pool import SubscriberQueue
from magg.magg_schemas import PlotDevelopmentAction, SimpleComment, SimpleDescription, WorldIntervention, PlotFollowingIntervention
from magg.plot_schemas import Chapter, ChapterStatus
from skls_generator.generator import Generator
from schemas.orchestration import Event, Message
from game.manipulators.base_manipulation import Archive

# Construct the absolute path to the prompts file
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROMPTS_PATH = os.path.join(os.path.dirname(_CURRENT_DIR), "prompts", "DM_personality.md")

class Magg:
    with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
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
        for i, e in enumerate(events):
            events_str += f"Event {i+1}: {str(e.dict())}\n"
        return events_str

    def inject_state(self, state : 'Session') -> None:
        self._session = state
        
    def get_simple_description(self) -> str:
        if self.session is None:
            raise ValueError("Session not injected into Magg")
        
        prompt = f"""
        {self.character_prompt}
        Generate a vivid description of the current scene in the DND game.
        ## Game state:
        {self.session.get_session_context()}
        
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
    
    def comment(self, events : list[Event]) -> str:
        """Generates a concise comment about recent events in the game."""
        self.event_queue.clear()
        
        events_str = self._events_to_string(events)
        prompt = f"""
### ROLE & PERSONA
{self.character_prompt}

### INSTRUCTIONS
Now is the stage when a character made their decision and you are commenting on the latest game events so make it accordingly to your personality. 

### Strict Requirements:
1. You MUST mention every value change (Health, Mana, Gold, etc.) listed in the events You must weave them into the description of the action (e.g., "The blow cost you 5 HP!" rather than "You lost 5 HP.").
2. Briefly acknowledge every event provided in the `<current_events>` block.
3. Do NOT mention internal engine data like coordinates (x,y).
4. Use the conversation history for context, but do not repeat what has already been said.
5. Provide necessary details. Make sure the user is aware of whats going on. You need to not only tell about completed events and also about characters intentions and requestes.

### CONTEXT
<game_state>
{self.session.get_session_context()}
</game_state>

<past_chat_history>
{self.session.get_messages_formatted()}
</past_chat_history>

### INPUT DATA
<current_events>
{events_str}
</current_events>

### YOUR RESPONSE
Based on the <current_events> above, generate your in-character comment:
"""
        self.logger.debug(f"event str is [{events_str}]")
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
        Politely ask for necessary details so that you can better understand their intentions in the game. You may also provide meta game details to a player e g their inventory or a list of spells. Suggest options if not clear.
        
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

    def comment_on_meta_request(self, request: str) -> str:
        """Handles meta requests/comments from players that are directed to the game master."""
        prompt = f"""{self.character_prompt}
        A player has made a meta request/comment: "{request}". Which is a request made on behalf of a user not their game character. So handle it respodingly.
        Respond to this meta request in character as the game master. This could be a question about the game,
        a request for information, or an out-of-character comment. Answer the question based on the game state or provide user the information they ask for. Take previous messages into consideration and use the context.

        # Conversation history for context:
        {self.session.get_messages_formatted()}
        
        # Current game state:
        {self.session.get_session_context()}
        """
        response = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        new_message = Message(
            sender_name="Mage",
            text=response.comment)
        self.session.new_message(new_message)
        return response.comment
    
    async def world_intervention(self, events : List[Event]):
        self.logger.debug("starting world intervention processing")
        prompt = f"""
## Input Data
You will receive:
1.  **Current Scene Assets:** A list of NPCs and Objects currently present.
2.  **Event Log:** The narrative description of what just happened (e.g., "The player killed the Goblin," "The Merchant walked away," "The player picked up the Rusty Key").

---

## Decision Logic

### 1. Identify Changes
Analyze the Event Log for specific triggers:

*   **Removal Triggers (Items leave the scene):**
    *   Player picks up an item (Add to Inventory $\rightarrow$ Remove from Scene).
    *   Item is destroyed/burnt/consumed.
    *   Item is hidden successfully.
*   **Addition Triggers (Items enter the scene):**
    *   Player drops an item.
    *   Player opens a chest/container (revealing contents).
    *   A hidden item is found via Perception/Investigation.
*   **NPC Arrival (NPCs enter the scene):**
    *   Reinforcements arrive.
    *   Summoning spells (e.g., "Conjure Animals").
    *   NPCs come out of hiding.

### 2. Consistency Rules
*   **Exact Names:** When removing items, you must use the **exact string match** from the "Current Scene Assets" list.
*   **No Hallucinations:** Do not add items that were not explicitly mentioned in the Event Log.
*   **Inventory is not the Scene:** If a player *has* a sword in their hand, it is in their Inventory, not the Scene list. Do not add it to the scene unless they drop it.

### 3. The `requires_scene_update` Flag
*   Set this to `True` **ONLY** if you are adding or removing items/NPCs, changing .
*   If the players just talked or looked around without changing the physical state, set to `False`.


## Session info:
{self.session.get_session_context()}


## Plot info and plans:
{self.session.plot}

## Recent events in the game:
{[f"{i}th event: {e.dict()} \n"  for i, e in enumerate(events)]}
"""
        res = self.generator.generate_one_shot(
            pydantic_model=WorldIntervention,
            prompt=prompt
        )        
        actions = []
        args = []
        if res.requires_intervention:
            
            # delete entities
            actions.append(self.session.manipulator._external_action_as_a_supervisor)
            args.append((f"entities (or objects) {res.removed_entity_names} must be removed from the scene",))
            
            #general changes
            actions.append(self.session.manipulator._external_action_as_a_supervisor)
            args.append((res.visual_description,))
            
            #new entites
            actions.append(self.session.manipulator._external_action_as_a_supervisor)
            args.append((f"npc characters {[npc.dict() for npc in res.new_npcs]} must be added to the scene",))
            
            #new objects
            actions.append(self.session.manipulator._external_action_as_a_supervisor)
            args.append((f"objects {res.new_objects} must be added to the scene",))
            
        async for event in run_list_in_parallel_generator(
            funcs=actions,
            args_list=args
        ):
            yield event
            
    async def check_plot_following(self, events : list[Event]):
        """
        Checks if the current game events align with the planned plot.
        Generates interventions if the players are deviating too much from the intended storyline.
        """
        # Only check plot following if a plot exists
        if not self.session._plot:
            self.logger.debug("No plot available, skipping plot following check")
            raise ValueError("No plot available, skipping plot following check")

        prompt = f"""
### ROLE & PERSONA
{self.character_prompt}

### OBJECTIVE
Analyze the recent game events and determine if the players are following the intended plotline.
Based on the analysis, decide on the appropriate plot development action.

### PLOT INFORMATION
Current Plot: {self.session.plot}

### RECENT EVENTS
{self._events_to_string(events)}

### GAME STATE
{self.session.get_session_context()}

### INSTRUCTIONS
Based on the plot and recent events, determine:
1. Should we create a new chapter? (CREATE_NEW_CHAPTER)
2. Should we update the current chapter's goals? (UPDATE_CURRENT_GOALS)
3. Should we escalate to the next chapter? (ESCALATE_TO_NEXT_CHAPTER)
4. Should we maintain the current chapter? (MAINTAIN_CURRENT_CHAPTER)
5. Should we fail the current chapter? (FAIL_CURRENT_CHAPTER)

Consider if the players have completed enough objectives to advance, if they're stuck and need guidance, 
or if they're going completely off track and need redirection.

Return a PlotFollowingIntervention response with the appropriate action and details.
"""

        res = self.generator.generate_one_shot(
            pydantic_model=PlotFollowingIntervention,
            prompt=prompt
        )

        if res.requires_intervention:
            self.logger.info(f"Plot following intervention required: {res.action.value} - {res.visual_description}")
            
            # Handle chapter progression based on the action
            if res.action.value == "CREATE_NEW_CHAPTER" and self.session._plot:
                if res.new_chapter_name:
                    new_chapter = Chapter(
                        name=res.new_chapter_name,
                        description=res.new_chapter_description or "",
                        tasks=res.new_chapter_tasks or {},
                        fail_conditions=res.new_chapter_fail_conditions or [],
                        status=ChapterStatus.COMING
                    )
                    self.session._plot.chapters.append(new_chapter)
                    self.logger.info(f"Created new chapter: {new_chapter.name}")
            
            elif res.action.value == PlotDevelopmentAction.UPDATE_CURRENT_GOALS and self.session._plot and res.updated_tasks:
                # Update the current chapter's tasks
                current_chapter = self.session._plot.current_chapter
                if current_chapter:
                    current_chapter.tasks.update(res.updated_tasks)
                    self.logger.info(f"Updated tasks for current chapter: {current_chapter.name}")
                    
            elif res.action.value == PlotDevelopmentAction.ESCALATE_TO_NEXT_CHAPTER and self.session._plot:
                # Mark current chapter as completed and move to next
                current_chapter = self.session._plot.current_chapter
                if current_chapter:
                    current_chapter.status = ChapterStatus.COMPLETED
                    self.logger.info(f"Escalated from chapter: {current_chapter.name}")
                    
            elif res.action.value == PlotDevelopmentAction.FAIL_CURRENT_CHAPTER and self.session._plot:
                # Mark current chapter as failed
                current_chapter = self.session._plot.current_chapter
                if current_chapter:
                    current_chapter.status = ChapterStatus.FAILED
                    self.logger.info(f"Failed current chapter: {current_chapter.name}")
            
            # Execute the intervention actions
            actions = []
            args = []
            
            # Remove entities if needed
            if res.removed_entity_names:
                actions.append(self.session.manipulator._external_action_as_a_supervisor)
                args.append((f"entities (or objects) {res.removed_entity_names} must be removed from the scene",))

            # Apply general changes
            actions.append(self.session.manipulator._external_action_as_a_supervisor)
            args.append((res.visual_description,))

            # Add new NPCs if needed
            if res.new_npcs:
                actions.append(self.session.manipulator._external_action_as_a_supervisor)
                args.append((f"npc characters {[npc.dict() for npc in res.new_npcs]} must be added to the scene",))

            # Add new objects if needed
            if res.new_objects:
                actions.append(self.session.manipulator._external_action_as_a_supervisor)
                args.append((f"objects {res.new_objects} must be added to the scene",))

            async for event in run_list_in_parallel_generator(
                funcs=actions,
                args_list=args
            ):
                yield event
        else:
            self.logger.debug("No plot following intervention required")


    async def handle_events(self):
        """Handles events produced after each game turn in any game mode and creates Game Master commnts 
        on events produced by the game. It also initiates external wold changes triggered by the game master."""
        events = self.event_queue.get_all()
        self.event_queue.clear()
        self.logger.debug("running world_intervention, comment, and check_plot_following in parallel")
        comment = None
        
        async for result in run_list_in_parallel_generator(
            funcs=[
                self.world_intervention,
                self.comment,
                self.check_plot_following
                ],
            args_list=[
                (events,),
                (events,),
                (events,)
            ]
        ):
            if isinstance(result, Event):
                self.logger.debug(f"Event produced {result.description[:10]}...")
                self.event_queue.publish_to_others(result)
            elif isinstance(result, str):
                self.logger.debug(f"Comment produced {result[:10]}...")
                comment = result
            # Note: check_plot_following yields events which are handled as above

        return comment