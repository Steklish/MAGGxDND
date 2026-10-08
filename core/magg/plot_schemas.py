from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

    
class ChapterStatus(str, Enum):
    COMING = "COMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"

class Chapter(BaseModel):
    name : str = Field(description="A chapter name (must be short and unique)")
    description : str = Field(description="Text description of events planned.")
    tasks : dict[str, bool] = Field(description="List of tasks to be accomplished in this chapter. (with completeion status)")
    fail_conditions : list[str] = Field(description="A lit of conditions that instantly fail chapter progress")
    status : ChapterStatus = Field(description="Chapter status.")
    
class Plot(BaseModel):
    world_description : str = Field(description="A brief description of the world. INcule only the details that differ the current wprl from an average dnd fantasy environment.")
    chapters : List[Chapter] = Field(description="A list of chapters that are expected to happen in the story.")
    status : ChapterStatus = Field(description="Chapter status describing how to handle a capter.")
    # current_chapter : Chapter = Field(description="A pointer to the current chapter")
    @computed_field
    @property
    def current_chapter(self) -> Chapter | None:
        for c in self.chapters:
            if c.status == ChapterStatus.COMING:
                return c
        return None


def generate_default_plot(prompt_or_title: str = "", language: str = "ru") -> Plot:
    """Generate a coherent 3-chapter D&D adventure plot with tasks and fail conditions in the desired language."""
    p_lower = (prompt_or_title or "").lower()
    is_ru = (language or "ru").lower().startswith("ru")

    if any(k in p_lower for k in ["crypt", "tomb", "dread", "undead", "skeleton", "death", "shadow", "grave", "necromanc", "склеп", "могил", "мертвец", "нежит"]):
        if is_ru:
            world = "Забытое баронство вечной тьмы, где мертвецы не знают покоя, а некротический туман клубится над древними катакомбами."
            ch1 = Chapter(
                name="Глава 1: Пробуждение в склепе",
                description="Проникнуть за порог древней усыпальницы, осмотреть архитектуру в поисках тайн и одолеть дозорных скелетов.",
                tasks={
                    "Осмотреть стены зала и каменные саркофаги в поисках скрытых подсказок или ловушек": False,
                    "Обезвредить или обойти рыскающих скелетов-дозорных": False,
                    "Отпереть тяжелые железные ворота во внутреннее святилище": False,
                },
                fail_conditions=["Весь отряд пал в бою", "Вход в склеп окончательно обрушился"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Глава 2: Зал Шепотов",
                description="Преодолеть заминированные катакомбы, развеять защитные чары и добыть замковый камень святилища.",
                tasks={
                    "Расшифровать древние арканные надписи вдоль коридора": False,
                    "Одолеть теневых призраков, охраняющих ритуальные урны": False,
                    "Заполучить рунический камень-ключ от главного хранилища": False,
                },
                fail_conditions=["Проклятие нежити поглощает рассудок отряда", "Гибель отряда"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Глава 3: Пробуждение Владыки Тьмы",
                description="Сразиться с Владыкой Тьмы в центральном мавзолее и навсегда разрушить темный некротический нексус.",
                tasks={
                    "Прервать темный ритуал, питающий склеп силой": False,
                    "Победить Владыку Тьмы в решающем бою": False,
                    "Покинуть рушащееся святилище с древней реликвией": False,
                },
                fail_conditions=["Владыка Тьмы обретает бессмертие", "Святилище хоронит героев под обломками"],
                status=ChapterStatus.COMING
            )
        else:
            world = "A desolate forgotten barony where the dead do not rest easily and necrotic mists linger above ancient catacombs."
            ch1 = Chapter(
                name="Chapter 1: The Crypt Unsealed",
                description="Infiltrate the threshold of the ancient crypt, examine the architecture for secrets, and defeat the perimeter sentinels.",
                tasks={
                    "Survey the chamber walls and stone sarcophagi for hidden clues or traps": False,
                    "Neutralize or evade lurking skeletal sentinels": False,
                    "Unseal the heavy iron gate leading to the inner sanctuary": False,
                },
                fail_conditions=["The entire party falls in battle", "The entryway collapses permanently"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Chapter 2: The Hall of Whispers",
                description="Navigate through trapped catacombs, decipher the necrotic wards, and collect the sanctum keystone.",
                tasks={
                    "Decipher the ancient arcane inscriptions lining the corridor": False,
                    "Overcome the shadow apparitions guarding the ritual urns": False,
                    "Acquire the runic keystone needed to unlock the master vault": False,
                },
                fail_conditions=["The necrotic curse overwhelms the party", "The party wipes out"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Chapter 3: The Dread Lord's Awakening",
                description="Confront the Dread Lord in the central sepulcher and shatter the necrotic nexus forever.",
                tasks={
                    "Disrupt the dark ritual binding the crypt's power": False,
                    "Defeat the Dread Lord in decisive combat": False,
                    "Escape the collapsing sanctuary with the ancient relic": False,
                },
                fail_conditions=["The Dread Lord attains godhood", "The sanctuary collapses on the party"],
                status=ChapterStatus.COMING
            )
    elif any(k in p_lower for k in ["tavern", "inn", "city", "town", "urban", "thief", "guild", "market", "таверн", "трактир", "город", "привал"]):
        if is_ru:
            world = "Оживленный приграничный город, раздираемый контрабандистами, враждой воровских гильдий и слухами о перевороте."
            ch1 = Chapter(
                name="Глава 1: Тени в таверне",
                description="Собрать сведения в таверне, допросить подозрительных завсегдатаев и утихомирить пьяную драку наемников.",
                tasks={
                    "Подслушать разговоры или расспросить посетителей о ночных грузах": False,
                    "Утихомирить буйных наемников, затеявших драку в зале": False,
                    "Заполучить зашифрованный гроссбух, оброненный курьером синдиката": False,
                },
                fail_conditions=["Таверна сгорела дотла", "Курьер синдиката скрылся незамеченным"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Глава 2: Подполье контрабандистов",
                description="Выследить синдикат в каменных коллекторах и проникнуть на их тайный склад.",
                tasks={
                    "Пройти через затопленные туннели, не подняв тревогу": False,
                    "Обезвредить механические растяжки и ловушки": False,
                    "Проникнуть в секретное хранилище контрабанды": False,
                },
                fail_conditions=["Поднята тревога по всему кварталу", "Отряд схвачен стражей"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Глава 3: Расплата главы гильдии",
                description="Загнать теневого вдохновителя в угол в его сокровищнице и положить конец преступной сети.",
                tasks={
                    "Встретиться лицом к лицу с продажным главой гильдии": False,
                    "Одолеть элитных телохранителей мафиози": False,
                    "Защитить городскую казну от разграбления": False,
                },
                fail_conditions=["Глава синдиката сбегает по морю"],
                status=ChapterStatus.COMING
            )
        else:
            world = "A bustling border town plagued by smuggling rings, guild rivalries, and whispers of an impending syndicate coup."
            ch1 = Chapter(
                name="Chapter 1: Shadows in the Taproom",
                description="Gather intelligence in the tavern, interrogate the suspicious patrons, and quell the tavern brawl.",
                tasks={
                    "Eavesdrop or question the patrons about suspicious nightly shipments": False,
                    "Subdue the belligerent mercenaries instigating a tavern brawl": False,
                    "Retrieve the coded ledger dropped by the syndicate courier": False,
                },
                fail_conditions=["The tavern is burnt down", "The syndicate courier escapes undetected"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Chapter 2: The Smuggler's Underbelly",
                description="Track the syndicate down into the cobblestone sewers and breach their covert warehouse.",
                tasks={
                    "Navigate the flooded sewer maze without alerting alarms": False,
                    "Disable the mechanical tripwires and dart traps": False,
                    "Infiltrate the secret contraband depot": False,
                },
                fail_conditions=["The alarm sounds across the entire district", "Party capture"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Chapter 3: The Guildmaster's Reckoning",
                description="Corner the shadowy mastermind in their vault and dismantle the syndicate network.",
                tasks={
                    "Confront the corrupt guildmaster and demand answers": False,
                    "Defeat the guildmaster's elite bodyguards": False,
                    "Secure the municipal treasury before it is smuggled out": False,
                },
                fail_conditions=["The syndicate escapes by sea"],
                status=ChapterStatus.COMING
            )
    else:
        # Default heroic adventure
        if is_ru:
            world = "Классический мир высокого темного фэнтези, где опасности таятся в древних руинах, а слава ждёт смелых искателей приключений."
            ch1 = Chapter(
                name="Глава 1: Первые испытания",
                description="Осмотреть вход в подземелье, обнаружить скрытые проходы и одолеть передовой дозор защитников.",
                tasks={
                    "Осмотреть зал в поисках подсказок, тайных механизмов или выходов": False,
                    "Сразиться и нейтрализовать враждебных стражей, охраняющих область": False,
                    "Отыскать проход, ведущий в таинственные подземные глубины": False,
                },
                fail_conditions=["Отряд искателей приключений пал в бою", "Свод пещеры обрушился"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Глава 2: Испытания Лабиринта",
                description="Продвинуться вглубь опасного комплекса, разгадать испытания стражей и завладеть древней реликвией.",
                tasks={
                    "Обезвредить или обойти хитроумную напольную ловушку": False,
                    "Одолеть чудовищного стража, обитающего в центральном зале": False,
                    "Заполучить реликвию-ключ, необходимую для продвижения": False,
                },
                fail_conditions=["Отряд истощил силы и пал от изнеможения"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Глава 3: Решающая битва",
                description="Сразиться с владыкой подземелья, сокрушить его темные замыслы и выйти победителями.",
                tasks={
                    "Разрушить магический барьер, защищающий святилище": False,
                    "Одолеть главного босса подземелья в эпическом поединке": False,
                    "Забрать древнее сокровище и триумфально вернуться назад": False,
                },
                fail_conditions=["Владыка высвобождает губительное проклятие"],
                status=ChapterStatus.COMING
            )
        else:
            world = "A classic realm of high fantasy where danger lurks in ancient ruins and glory awaits bold adventurers."
            ch1 = Chapter(
                name="Chapter 1: The First Expedition",
                description="Survey the dungeon entrance, look for traps or hidden pathways, and overcome the first line of defenders.",
                tasks={
                    "Investigate the chamber for clues, exits, or hidden mechanisms": False,
                    "Engage and neutralize the hostile sentinels guarding the area": False,
                    "Discover the passageway leading into the subterranean depths": False,
                },
                fail_conditions=["The expedition party is defeated", "The cavern roof collapses"],
                status=ChapterStatus.COMING
            )
            ch2 = Chapter(
                name="Chapter 2: Trials of the Labyrinth",
                description="Venture deeper into the perilous complex, solve the guardian trials, and obtain the relic keystone.",
                tasks={
                    "Solve or bypass the intricate floor trap mechanism": False,
                    "Defeat the guardian beast dwelling in the grand hall": False,
                    "Acquire the relic keystone necessary to proceed": False,
                },
                fail_conditions=["The party runs out of supplies and succumbs to exhaustion"],
                status=ChapterStatus.COMING
            )
            ch3 = Chapter(
                name="Chapter 3: The Final Confrontation",
                description="Confront the dungeon's master, shatter their dark ambitions, and emerge victorious.",
                tasks={
                    "Disrupt the magical ward protecting the inner sanctuary": False,
                    "Defeat the dungeon boss in an epic showdown": False,
                    "Claim the ancient treasure and return in triumph": False,
                },
                fail_conditions=["The boss unleashes an apocalyptic curse"],
                status=ChapterStatus.COMING
            )

    return Plot(
        world_description=world,
        chapters=[ch1, ch2, ch3],
        status=ChapterStatus.COMING
    )