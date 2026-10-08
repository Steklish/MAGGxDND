from logging import Logger
from typing import TYPE_CHECKING, List, Optional
import os
import asyncio

from core.utils.threads import run_list_in_parallel, run_list_in_parallel_generator
if TYPE_CHECKING:
    from core.game.engine import Session
from core.game.event_pool import SubscriberQueue
from core.magg.magg_schemas import PlotDevelopmentAction, SimpleComment, SimpleDescription, WorldIntervention, PlotFollowingIntervention
from core.magg.plot_schemas import Chapter, ChapterStatus
from skls_generator.generator import Generator
from core.schemas.orchestration import Event, Message
from core.game.manipulators.base_manipulation import Archive

# Get project root directory - go up 2 levels from core/magg/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class Magg:
    with open(os.path.join(PROJECT_ROOT, "docs/prompts/DM_personality.md"), "r", encoding="utf-8") as f:
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

    def _get_language_directive(self) -> str:
        lang = getattr(self.session, "language", "ru") if self._session else "ru"
        if lang == "ru":
            return (
                "### ЯЗЫКОВАЯ ДИРЕКТИВА (СТРОЖАЙШЕЕ ОБЯЗАТЕЛЬНОЕ ПРАВИЛО):\n"
                "ТЫ ОБЯЗАН ВЕСТИ ВСЁ ПОВЕСТВОВАНИЕ ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ!\n"
                "- Все описания сцен, действий персонажей, чувств, ощущений, ранений и диалогов должны быть на богатом, живом, литературном русском языке.\n"
                "- Категорически запрещено отвечать на английском языке.\n\n"
            )
        else:
            return (
                "### LANGUAGE DIRECTIVE (MANDATORY REQUIREMENT):\n"
                "You MUST generate the entire narrative, descriptions, and dialogue in ENGLISH.\n\n"
            )

    def inject_state(self, state : 'Session') -> None:
        self._session = state
        
    def get_simple_description(self) -> str:
        if self.session is None:
            raise ValueError("Session not injected into Magg")
        
        prompt = f"""
        {self._get_language_directive()}
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
        
        if not getattr(self.session, "delivery", None):
            self.session.new_message(Message(sender_name="GM", text=description.description))

        return description.description
    
    def comment(self, events : list[Event]) -> str:
        """Generates a narrative description of recent events in D&D style."""
        self.event_queue.clear()

        events_str = self._events_to_string(events)
        prompt = f"""
{self._get_language_directive()}
### ROLE & PERSONA
{self.character_prompt}

### INSTRUCTIONS
You are the **primal link between the game world and the players**. Your task is to **narrate the events** as they unfold in the game world. Do NOT comment on events from the outside - instead, **describe them as they happen** in vivid D&D narrative style.

Think of yourself as the **eyes and ears of the players in the game world**. When a character acts, you describe that action as if the players are witnessing it firsthand. Your narration should be immersive, comprehensive, and make the players feel like they are there.

**Key Principle:** You are NOT an observer commenting on what happened. You ARE the voice of the game world itself, describing actions as they unfold.

### Strict Requirements:
1. **Narrate, don't comment:** Describe actions as they happen (e.g., "The worm's slimy body glides silently across the dusty floor, leaving a glistening trail as it approaches the cold fireplace") NOT as meta-commentary (e.g., "Ах, этот червяк! Ползает, как змея в траве. Интересно, что он задумал?").
2. **NO Direct Name Addressing:** Do NOT constantly repeat character names like a commentator. Use descriptive references instead: "the wizard," "the worm," "the warrior," "your companion," "the creature," "the beast." Describe entities by what they ARE, not what they're called.
3. **Mention every value change:** You MUST weave stat changes (Health, Mana, Gold, etc.) into the narrative naturally (e.g., "The blade bites deep — 5 HP lost in a crimson spray!" rather than "You lost 5 HP").
4. **Cover every event:** Acknowledge and narrate every event provided in the `<current_events>` block.
5. **NO internal engine data:** Do NOT mention coordinates, event types, or other meta information.
6. **Use context:** Draw from conversation history for context, but do not repeat what has already been narrated.
7. **Be comprehensive:** Provide rich sensory details — what the players see, hear, smell, feel. Make the world come alive.
8. **D&D narrative style:** Use dramatic, immersive language fitting for a Dungeons & Dragons game. Describe intentions, actions, and consequences as a cohesive narrative.
9. **Keep players oriented:** Always make sure players understand what is happening in the game world. Leave no ambiguity about the current situation.

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
Based on the <current_events> above, generate your immersive D&D narrative describing these events as they unfold:
"""
        self.logger.debug(f"event str is [{events_str}]")
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        
        if not getattr(self.session, "delivery", None):
            self.session.new_message(Message(sender_name="GM", text=comment.comment))

        return comment.comment
    
    def illegal_action_comment(self, prompt, reasoning, name) -> str:
        prompt = f"""{self._get_language_directive()}
        {self.character_prompt} 
        You need to comment on the illegal action attempted by players in a concise manner. (illigal due to {reasoning})
        
        # there is also past conversation history provided with your answers included (use it for natural conversation flow):
        {self.session.get_messages_formatted()}
        """
        comment = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        if not getattr(self.session, "delivery", None):
            self.session.new_message(Message(sender_name="GM", text=comment.comment))
        return comment.comment
    
    def clarify_user_request(self, correction_question : str) -> str:
        prompt = f"""{self._get_language_directive()}
        {self.character_prompt}
        You need to ask the last playerfor clarification on their request: "{correction_question}".
        Politely ask for necessary details so that you can better understand their intentions in the game. You may also provide meta game details to a player e g their inventory or a list of spells. Suggest options if not clear.
        
        # there is also past conversation history provided with your answers included  (the last user rquest needs clarification to follow game rules more properly):
        {self.session.get_messages_formatted()}
        """
        clarification = self.generator.generate_one_shot(
            pydantic_model=SimpleComment,
            prompt=prompt
        )
        if not getattr(self.session, "delivery", None):
            self.session.new_message(Message(sender_name="GM", text=clarification.comment))
        return clarification.comment

    def comment_on_meta_request(self, request: str) -> str:
        """Handles meta requests/comments from players that are directed to the game master."""
        prompt = f"""{self._get_language_directive()}
        {self.character_prompt}
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
        if not getattr(self.session, "delivery", None):
            self.session.new_message(Message(sender_name="GM", text=response.comment))
        return response.comment
    
    async def world_intervention(self, events : List[Event]):
        self.logger.debug("starting world intervention processing")
        prompt = f"""{self._get_language_directive()}
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
            
        for func, arg in zip(actions, args):
            try:
                events_list = func(*arg)
                if isinstance(events_list, list):
                    for event in events_list:
                        yield event
                elif isinstance(events_list, Event):
                    yield events_list
            except Exception as exc:
                self.logger.warning(f"Error executing supervisor action: {exc}")
            
    async def check_plot_following(self, events : list[Event]):
        """
        Checks if the current game events align with the planned plot.
        Generates interventions if the players are deviating too much from the intended storyline.
        """
        # Only check plot following if a plot exists
        if not self.session._plot:
            self.logger.debug("No plot available, skipping plot following check")
            return

        prompt = f"""
{self._get_language_directive()}
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

            for func, arg in zip(actions, args):
                try:
                    events_list = func(*arg)
                    if isinstance(events_list, list):
                        for event in events_list:
                            yield event
                    elif isinstance(events_list, Event):
                        yield events_list
                except Exception as exc:
                    self.logger.warning(f"Error executing supervisor action: {exc}")
        else:
            self.logger.debug("No plot following intervention required")


    async def handle_events(self):
        """Handles events produced after each game turn in any game mode and creates Game Master comments
        on events produced by the game. It also initiates external world changes triggered by the game master."""
        events = self.event_queue.get_all()
        self.event_queue.clear()

        if not events:
            # Nothing to process — don't waste AI calls on empty input
            self.logger.debug("[MAGG] handle_events: no events to process, skipping")
            return None

        self.logger.debug("Running Game Master comment, world intervention, and plot check")
        comment = None

        # 1. Generate Game Master narrative comment
        try:
            comment = await asyncio.to_thread(self.comment, events)
            self.logger.debug(f"Comment produced: {comment[:40] if comment else 'None'}...")
        except Exception as e:
            self.logger.error(f"Error generating Game Master comment: {e}", exc_info=True)
            is_ru = getattr(self.session, "language", "ru") == "ru"
            if events:
                last_event_desc = events[-1].description or ("Действие возымело эффект." if is_ru else "The action takes effect.")
                comment = f"Пока события разворачиваются: {last_event_desc}" if is_ru else f"As events unfold, {last_event_desc}"
            else:
                comment = "Вы берете мгновение, чтобы оценить обстановку." if is_ru else "You take a moment to assess the situation."

        # 2. Check world intervention
        try:
            async for result in self.world_intervention(events):
                if isinstance(result, Event):
                    self.logger.debug(f"World intervention event produced: {result.description[:30]}...")
                    self.event_queue.publish_to_others(result)
        except Exception as e:
            self.logger.error(f"Error in world intervention: {e}", exc_info=True)

        # 3. Check plot following (only if plot exists)
        if self.session._plot:
            try:
                async for result in self.check_plot_following(events):
                    if isinstance(result, Event):
                        self.logger.debug(f"Plot intervention event produced: {result.description[:30]}...")
                        self.event_queue.publish_to_others(result)
            except Exception as e:
                self.logger.error(f"Error in plot following: {e}", exc_info=True)

        return comment