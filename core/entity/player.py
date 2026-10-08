from logging import Logger
from typing import TYPE_CHECKING

from core.game.event_pool import SubscriberQueue
from core.interface.delivery import Delivery
from core.schemas.orchestration import Event, Message, OrchestrationVerdictType, UserInterationType
if TYPE_CHECKING:
    from core.game.engine import Session
from core.entity.orchestrator import Orchestrator
from core.schemas.in_game import Character, GameModes
from core.entity.game_entity import GameEntity


MAX_LEN = 1000

class Player(GameEntity):
    def __init__(self, character: Character,
                 event_queuee : SubscriberQueue,
                 logger: Logger,
                 orchestrator: Orchestrator,
                 ) -> None:
        super().__init__(character, event_queuee, logger)
        self.orchestrator = orchestrator
        self.character : Character
        self.is_ai_controlled: bool = getattr(character, 'is_ai_controlled', False)
        # string used for context if character clarifications or rules checks 
        # were interrupted by another player (used for run_story) 
        # should be cleaned after action is complete
        self._input_cache : str = "" 

    def _generate_ai_companion_action(self) -> str:
        """Generate contextual tactical/narrative action when character is under AI control."""
        import random
        name = self.character.name
        char_class = getattr(self.character, 'char_class', 'Fighter')
        class_str = char_class.value if hasattr(char_class, 'value') else str(char_class)
        scene_name = getattr(self.session.current_scene, 'name', 'the area')
        lang = getattr(self.session, 'language', 'ru') if self.session else 'ru'

        if lang == 'ru':
            class_actions_ru = {
                "Fighter": [
                    f"Я поднимаю щит, держу строй рядом с соратниками и прикрываю авангард в {scene_name}.",
                    f"Я обнажаю оружие и делаю выпад на 10 футов вперед, прикрывая отряд от засад.",
                    f"Я принимаю оборонительную стойку и внимательно высматриваю приближающихся врагов."
                ],
                "Wizard": [
                    f"Я остаюсь за спинами союзников, готовлю магический фокус и изучаю окружение.",
                    f"Я сканирую зал на наличие магических аур и тайных рун.",
                    f"Я держу наготове защитное заклинание, соблюдая безопасную дистанцию."
                ],
                "Rogue": [
                    f"Я бесшумно скольжу в тени и проверяю периметр на наличие ловушек и потайных дверей.",
                    f"Я укрываюсь за выступом и внимательно слежу за путями отхода.",
                    f"Я осторожно осматриваю местность и подаю знак соратникам быть начеку."
                ],
                "Cleric": [
                    f"Я взываю к божественной защите и держу священный символ, оберегая отряд.",
                    f"Я слежу за состоянием соратников и готов немедленно исцелить раненых.",
                    f"Я благословляю наш путь и всматриваюсь во тьму в поисках нежити или проклятий."
                ]
            }
            options = class_actions_ru.get(class_str, [
                f"Я сохраняю бдительность рядом с отрядом и слежу за опасностями в {scene_name}.",
                f"Я осторожно продвигаюсь вперед вместе с соратниками, держа оружие наготове."
            ])
            return random.choice(options)

        class_actions_en = {
            "Fighter": [
                f"I raise my shield, stay beside my companions, and hold the frontline in {scene_name}.",
                f"I draw my weapon and advance 10 feet forward to guard the party against ambushes.",
                f"I take a defensive stance and scan the area for incoming hostiles."
            ],
            "Wizard": [
                f"I stay behind the frontline, prepare my arcane focus, and observe the surroundings.",
                f"I scan the chamber for magical auras or arcane runes.",
                f"I ready a defensive cantrip while keeping a safe distance."
            ],
            "Rogue": [
                f"I quietly search the shadows and check the perimeter for traps and hidden doors.",
                f"I slip into cover and keep a vigilant eye on potential escape routes.",
                f"I examine the terrain cautiously and signal my allies to stay alert."
            ],
            "Cleric": [
                f"I pray for divine guidance and keep my holy symbol close to protect the party.",
                f"I check on my companions' conditions and hold ready to assist anyone wounded.",
                f"I bless our path forward and watch for unholy or cursed presence."
            ]
        }
        options = class_actions_en.get(class_str, [
            f"I stay alert with the party and watch for immediate dangers in {scene_name}.",
            f"I advance cautiously with my companions, weapons at the ready."
        ])
        return random.choice(options)
        
    @property
    def input_cache(self) -> str:
        return self._input_cache

    @input_cache.setter
    def input_cache(self, value: str) -> None:
        # assign new value
        buf = value

        # if too long, drop whole lines from the left at '\n'
        if len(buf) > MAX_LEN:
            # keep only last MAX_LEN chars as a starting point
            buf = buf[-MAX_LEN:]

            # try to drop a partial leading line, if any
            first_newline = buf.find("\n")
            if first_newline != -1:
                # drop everything up to and including that newline
                buf = buf[first_newline + 1 :]

        self._input_cache = buf

        
    def run_story(self) -> bool:
        """A method that runs character in story mode. If an input doesn't result to an acceptable action it releases the game loop instead of blocking it like self.run().
        Returns True if action was directly handled with a DM response (or skipped/errored), or False if action events were published for MAGG narration."""
        try:
            if self.is_ai_controlled:
                request = self._generate_ai_companion_action()
                self.logger.info(f"[AI-COMPANION] {self.character.name} executing story turn via AI: '{request}'")
            else:
                request = self.session.delivery.player_request(self.character)

            if request.strip() == "":
                # Skip turn - return empty list of events
                return True

            new_message = Message(
                sender_name=self.character.name,
                text=request)
            self.session.new_message(new_message)

            user_interaction = self.orchestrator.request(
                username=self.character.name,
                request_text=request,
                message_cahce=self._input_cache
            )
            executed_events = []
            if user_interaction.interaction_type == UserInterationType.CHARACTER_ACTION:
                if self.session.game_mode == GameModes.COMBAT:
                    verdict = self.orchestrator.character_action_combat(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )
                else:
                    verdict = self.orchestrator.character_action_story(
                        character=self,
                        request_text=request,
                        processed_interaction=user_interaction
                    )
                    
                if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                    events = self.session.manipulator._external_action_as_an_entity(verdict.details if verdict.details else request, self)
                    executed_events.extend(self.session.manipulator.execute_events(events))
                    self._input_cache = ""
                    # Publish ALL events produced by orchestrator — even if no manipulator
                    # handled them, MAGG should still be able to comment on them.
                    all_to_publish = executed_events if executed_events else events
                    self.logger.info(f"[run_story] Publishing {len(all_to_publish)} events for {self.character.name}")
                    for e in all_to_publish:
                        self.event_queue.publish_to_others(e)
                    self.logger.info(f"[run_story] Events published, event_pool now has {len(self.session.event_pool.get_events())} events")
                    return False
                elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                    # Unclear action - need clarification from user
                    # Send clarification request to game master
                    clarification_response = self.session.game_master.clarify_user_request(
                        correction_question=verdict.details if verdict.details else "Action needs clarification"
                    )
                    self.session.delivery.master_message(
                        text=clarification_response,
                        tag="Clarification"
                    )
                    self._input_cache += f"""{self.character.name} sent: {request} \n master's clarification request: {clarification_response}\n"""
                    return True
                
                elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                    # Illegal action - request a new one
                    illegal_response = self.session.game_master.illegal_action_comment(
                        prompt=request,
                        name=self.character.name,
                        reasoning=verdict.details if verdict.details else "Action is not allowed"
                    )
                    self.session.delivery.master_message(
                        text=illegal_response,
                        tag="Illegal"
                    )
                    self._input_cache += f"""{self.character.name} sent: {request} \n master's illegal comment on the previous request: {illegal_response}\n"""
                    return True
                
            elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                # Meta comment - this is a direct question/query to the game master
                # Process it and continue the loop to get an actual action
                meta_response = self.session.game_master.comment_on_meta_request(request)
                self.session.delivery.master_message(
                    text=meta_response,
                    tag="Meta"
                )
                self._input_cache += f"""{self.character.name} sent: {request} \n master's meta comment: {meta_response}\n"""
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error executing story turn for {self.character.name}: {e}", exc_info=True)
            is_ru = getattr(self.session, "language", "ru") == "ru"
            fallback_text = (
                f"⚠️ *Магическая связь с миром исказилась из-за помех в магии (ошибка ИИ). {self.character.name} сохраняет концентрацию.*"
                if is_ru else
                f"⚠️ *The magical weave fluctuated due to an AI service error. {self.character.name} maintains focus.*"
            )
            if self.session.delivery:
                self.session.delivery.master_message(text=fallback_text, tag="SystemError")
                self.session.delivery.session_updated(self.session)
            return True
    
    def run(self):
        """Player's turn. Returns a list of events based on player action.
        Handles three possible outcomes: legal action, unclear action needing clarification,
        and illegal action requiring a new one."""
        self.session.delivery.draw_ascii_scene(self.session)
        # just in case it stores really old cache not useful after the combat ends
        self._input_cache = "" 
        try:
            while True:
                if self.is_ai_controlled:
                    request = self._generate_ai_companion_action()
                    self.logger.info(f"[AI-COMPANION] {self.character.name} executing combat turn via AI: '{request}'")
                else:
                    self.logger.debug(f"Waiting for player input for {self.character.name}")
                    request = self.session.delivery.player_request(self.character)

                if request.strip() == "":
                    # Skip turn - return empty list of events
                    return

                new_message = Message(
                    sender_name=self.character.name,
                    text=request)
                self.session.new_message(new_message)

                user_interaction = self.orchestrator.request(
                    username=self.character.name,
                    request_text=request
                )
                executed_events = []
                if user_interaction.interaction_type == UserInterationType.CHARACTER_ACTION:
                    if self.session.game_mode == GameModes.COMBAT:
                        verdict = self.orchestrator.character_action_combat(
                            character=self,
                            request_text=request,
                            processed_interaction=user_interaction
                        )
                    else:
                        verdict = self.orchestrator.character_action_story(
                            character=self,
                            request_text=request,
                            processed_interaction=user_interaction
                        )
                    if verdict.verdict_type == OrchestrationVerdictType.ALLOWED_PLAYER_ACTION:
                        events = self.session.manipulator._external_action_as_an_entity(verdict.details if verdict.details else request, self)
                        executed_events.extend(self.session.manipulator.execute_events(events))
                        break

                    elif verdict.verdict_type == OrchestrationVerdictType.CLAIRIFICATION_NEEDED:
                        # Unclear action - need clarification from user
                        # Send clarification request to game master
                        clarification_response = self.session.game_master.clarify_user_request(
                            correction_question=verdict.details if verdict.details else "Action needs clarification"
                        )
                        self.session.delivery.master_message(
                            text=clarification_response,
                            tag="Clarification"
                        )
                        return
                    elif verdict.verdict_type == OrchestrationVerdictType.ILLEGAL_PLAYER_ACTION:
                        # Illegal action - request a new one
                        illegal_response = self.session.game_master.illegal_action_comment(
                            prompt=request,
                            name=self.character.name,
                            reasoning=verdict.details if verdict.details else "Action is not allowed"
                        )
                        self.session.delivery.master_message(
                            text=illegal_response,
                            tag="Illegal"
                        )
                        return
                elif user_interaction.interaction_type == UserInterationType.META_COMMENT:
                    # Meta comment - this is a direct question/query to the game master
                    # Process it and notify the player
                    meta_response = self.session.game_master.comment_on_meta_request(request)
                    self.session.delivery.master_message(
                        text=meta_response,
                        tag="Meta"
                    )
                    return
                
            for e in executed_events:
                self.event_queue.publish_to_others(e)
        except Exception as e:
            self.logger.error(f"Error executing combat turn for {self.character.name}: {e}", exc_info=True)
            is_ru = getattr(self.session, "language", "ru") == "ru"
            fallback_text = (
                f"⚠️ *Боевое действие {self.character.name} прервано помехами магии (ошибка ИИ).*"
                if is_ru else
                f"⚠️ *Combat action of {self.character.name} interrupted by arcane interference (AI error).*"
            )
            if self.session.delivery:
                self.session.delivery.master_message(text=fallback_text, tag="SystemError")
                self.session.delivery.session_updated(self.session)