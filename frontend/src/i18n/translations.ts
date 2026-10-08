export type SupportedLanguage = 'ru' | 'en';

export interface Translations {
    nav: {
        campaigns: string;
        lobby: string;
        profile: string;
        logout: string;
        adventurer: string;
        backToCampaigns: string;
    };
    auth: {
        title: string;
        subtitle: string;
        guestHeading: string;
        enterAsGuest: string;
        enterTheRealm: string;
        username: string;
        usernamePlaceholder: string;
        password: string;
        passwordPlaceholder: string;
        switchPassword: string;
        switchGuest: string;
        switchRegister: string;
        switchLogin: string;
        register: string;
        login: string;
        connecting: string;
        errorFillBoth: string;
    };
    lobby: {
        title: string;
        subtitle: string;
        createAdventure: string;
        activeCampaigns: string;
        quickPresets: string;
        noCampaigns: string;
        modalTitle: string;
        campaignName: string;
        campaignNamePlaceholder: string;
        scenePrompt: string;
        scenePromptPlaceholder: string;
        gameLanguage: string;
        russian: string;
        english: string;
        forgeBtn: string;
        forging: string;
        cancelBtn: string;
        enterCampaign: string;
        playersCount: string;
    };
    sessionLobby: {
        headline: string;
        activeSession: string;
        claimPrompt: string;
        rollNewHero: string;
        closeForm: string;
        heroName: string;
        heroNamePlaceholder: string;
        heroClass: string;
        heroRace: string;
        rollHeroBtn: string;
        claimHero: string;
        claimedByYou: string;
        aiControlled: string;
        occupiedBy: string;
        enterGame: string;
        partyRoster: string;
    };
    game: {
        storyFocus: string;
        splitView: string;
        mapFocus: string;
        dmThinking: string;
        heroCodex: string;
        currentChapter: string;
        objectives: string;
        viewQuests: string;
        hideQuests: string;
        nextObjective: string;
        allCompleted: string;
        completed: string;
        modeStory: string;
        modeCombat: string;
        connecting: string;
        connected: string;
        enterCombatTooltip: string;
        exitCombatTooltip: string;
        sceneDossier: string;
        questsTooltip: string;
        diceRollerTooltip: string;
    };
    chat: {
        storyFilter: string;
        storyEventsFilter: string;
        allFilter: string;
        rollsFilter: string;
        dmFilter: string;
        inputPlaceholder: string;
        actButton: string;
        resolving: string;
        fastCommands: string;
        clarifyPrompt: string;
        actions: {
            attack: string;
            attackDesc: string;
            attackPrompt: string;
            dash: string;
            dashDesc: string;
            dashPrompt: string;
            dodge: string;
            dodgeDesc: string;
            dodgePrompt: string;
            hide: string;
            hideDesc: string;
            hidePrompt: string;
            search: string;
            searchDesc: string;
            searchPrompt: string;
            help: string;
            helpDesc: string;
            helpPrompt: string;
            interact: string;
            interactDesc: string;
            interactPrompt: string;
            speak: string;
            speakDesc: string;
            speakPrompt: string;
        };
    };
    scene: {
        dossier: string;
        arena: string;
        environment: string;
        connectedExits: string;
        otherLocations: string;
        travelTo: string;
        objectsInScene: string;
        searchRoom: string;
        inspect: string;
        interact: string;
        regenerateMap: string;
        targetInAction: string;
        tacticalMenuTitle: string;
        closeMenu: string;
        cellActions: {
            moveCarefully: string;
            moveCarefullyDesc: string;
            sprintDash: string;
            sprintDashDesc: string;
            exploreSearch: string;
            exploreSearchDesc: string;
            takeCover: string;
            takeCoverDesc: string;
            aimTarget: string;
            aimTargetDesc: string;
        };
        objectActions: {
            interact: string;
            interactDesc: string;
            inspect: string;
            inspectDesc: string;
            openSearch: string;
            openSearchDesc: string;
            forceBreak: string;
            forceBreakDesc: string;
            useCover: string;
            useCoverDesc: string;
        };
        characterActions: {
            meleeAttack: string;
            meleeAttackDesc: string;
            rangedAttack: string;
            rangedAttackDesc: string;
            castSpell: string;
            castSpellDesc: string;
            assessThreat: string;
            assessThreatDesc: string;
            intimidate: string;
            intimidateDesc: string;
            speak: string;
            speakDesc: string;
            assist: string;
            assistDesc: string;
            healAid: string;
            healAidDesc: string;
            defend: string;
            defendDesc: string;
            dodge: string;
            dodgeDesc: string;
            disengage: string;
            disengageDesc: string;
            survey: string;
            surveyDesc: string;
        };
    };
    character: {
        heroTab: string;
        itemsTab: string;
        abilitiesTab: string;
        partyTab: string;
        hp: string;
        ac: string;
        speed: string;
        level: string;
        str: string;
        dex: string;
        con: string;
        int: string;
        wis: string;
        cha: string;
        equip: string;
        unequip: string;
        drop: string;
        transfer: string;
        useAbility: string;
        emptyParty: string;
        selectHeroPrompt: string;
    };
    dice: {
        title: string;
        roll: string;
        advantage: string;
        disadvantage: string;
        normal: string;
        history: string;
    };
    languageSelector: {
        title: string;
        current: string;
        ruLabel: string;
        enLabel: string;
        tooltip: string;
    };
}

export const translations: Record<SupportedLanguage, Translations> = {
    ru: {
        nav: {
            campaigns: 'Кампании',
            lobby: 'Зал Приключений',
            profile: 'Профиль',
            logout: 'Выйти',
            adventurer: 'Искатель приключений',
            backToCampaigns: '← Назад к кампаниям',
        },
        auth: {
            title: 'MAGGxDND',
            subtitle: 'Тактический D&D движок и летопись на базе ИИ',
            guestHeading: 'Быстрый вход в мир',
            enterAsGuest: 'Войти как гость',
            enterTheRealm: 'Войти в мир',
            username: 'Имя искателя / Никнейм',
            usernamePlaceholder: 'например, Торгрим Железностоп',
            password: 'Пароль',
            passwordPlaceholder: 'Введите ваш пароль',
            switchPassword: 'Использовать аккаунт с паролем',
            switchGuest: 'Войти как гость (быстрый старт)',
            switchRegister: 'Создать новый аккаунт',
            switchLogin: 'Уже есть аккаунт? Войти',
            register: 'Зарегистрироваться',
            login: 'Войти в систему',
            connecting: 'Врата открываются...',
            errorFillBoth: 'Пожалуйста, укажите имя пользователя и пароль.',
        },
        lobby: {
            title: 'Зал Приключений & Кампании',
            subtitle: 'Присоединяйтесь к активной летописи или выкуйте новое подземелье',
            createAdventure: 'Создать кампанию',
            activeCampaigns: 'Активные кампании',
            quickPresets: 'Быстрые сценарии приключений',
            noCampaigns: 'Активных кампаний пока нет. Создайте первую!',
            modalTitle: 'Создание новой кампании',
            campaignName: 'Название кампании',
            campaignNamePlaceholder: 'например, Тайны Забытого Склепа',
            scenePrompt: 'Стартовая сцена и окружение',
            scenePromptPlaceholder: 'Опишите начальную сцену (таверна, подземелье, древний лес...)',
            gameLanguage: 'Язык игры (DM, сюжет и персонажи)',
            russian: 'Русский (RU)',
            english: 'English (EN)',
            forgeBtn: 'Выковать кампанию',
            forging: 'Создание мира...',
            cancelBtn: 'Отмена',
            enterCampaign: 'Войти в кампанию',
            playersCount: 'Игроков',
        },
        sessionLobby: {
            headline: 'Сбор Отряда & Выбор Героя',
            activeSession: 'Активная сессия',
            claimPrompt: 'Выберите героя из списка для управления или создайте нового персонажа. Свободными героями управляет ИИ.',
            rollNewHero: 'Создать нового героя',
            closeForm: '✕ Закрыть форму',
            heroName: 'Имя героя',
            heroNamePlaceholder: 'например, Екатерина Буревестник',
            heroClass: 'Класс',
            heroRace: 'Раса',
            rollHeroBtn: 'Выковать героя и войти',
            claimHero: 'Взять управление',
            claimedByYou: 'Ваш персонаж',
            aiControlled: 'Под управлением ИИ',
            occupiedBy: 'Занят игроком',
            enterGame: 'Войти в игру',
            partyRoster: 'Состав отряда',
        },
        game: {
            storyFocus: 'Сюжет',
            splitView: 'Баланс',
            mapFocus: 'Карта',
            dmThinking: 'Мастер Подземелий ткет реальность...',
            heroCodex: 'Лист героя',
            currentChapter: 'Текущая глава',
            objectives: 'Задач',
            viewQuests: '▼ Задачи главы',
            hideQuests: '▲ Скрыть',
            nextObjective: 'След. задача',
            allCompleted: 'Все цели главы успешно завершены! 🎉',
            completed: 'ВЫПОЛНЕНО',
            modeStory: 'СЮЖЕТ',
            modeCombat: 'БОЙ',
            connecting: 'Подключение...',
            connected: 'В сети',
            enterCombatTooltip: 'Переключить режим в тактический бой',
            exitCombatTooltip: 'Завершить бой и вернуться к сюжету',
            sceneDossier: 'Досье сцены и окружение',
            questsTooltip: 'Цели и задачи текущей главы',
            diceRollerTooltip: 'Броски кубиков D&D 5e',
        },
        chat: {
            storyFilter: 'Сюжет и диалоги',
            storyEventsFilter: 'Сюжет + События',
            allFilter: 'Вся летопись',
            rollsFilter: 'Броски кубиков',
            dmFilter: 'Решения Мастера',
            inputPlaceholder: 'Опишите действие, слова или замысел вашего героя... (Enter для отправки)',
            actButton: 'Действовать',
            resolving: 'Мастер решает...',
            fastCommands: 'Быстрые действия',
            clarifyPrompt: 'Мастер Подземелий просит уточнить действие:',
            actions: {
                attack: 'Атаковать',
                attackDesc: 'Атаковать ближайшего врага оружием',
                attackPrompt: 'Я атакую ближайшего противника оружием.',
                dash: 'Рывок',
                dashDesc: 'Удвоить скорость перемещения в этот ход',
                dashPrompt: 'Я совершаю Рывок, удваивая скорость передвижения в этот ход.',
                dodge: 'Уклонение',
                dodgeDesc: 'Помеха на атаки врагов против вас',
                dodgePrompt: 'Я принимаю защитную стойку и уклоняюсь от вражеских атак.',
                hide: 'Скрытность',
                hideDesc: 'Проверка Ловкости (Скрытность) за укрытием',
                hidePrompt: 'Я пытаюсь скрыться в укрытии с проверкой Ловкости (Скрытность).',
                search: 'Обыск',
                searchDesc: 'Внимательный осмотр локации на тайники и ловушки',
                searchPrompt: 'Я внимательно осматриваю окружение с проверкой Внимательности / Анализа.',
                help: 'Помощь',
                helpDesc: 'Дать преимущество соратнику',
                helpPrompt: 'Я помогаю союзнику, давая преимущество на следующую атаку или проверку.',
                interact: 'Предмет',
                interactDesc: 'Активировать механизм или предмет сцены',
                interactPrompt: 'Я взаимодействую с ближайшим предметом или механизмом в сцене.',
                speak: 'Сказать',
                speakDesc: 'Произнести речь или реплику вслух',
                speakPrompt: 'Я говорю вслух: "',
            },
        },
        scene: {
            dossier: 'Тактическое досье локации',
            arena: 'Арена',
            environment: 'Окружение и повествование',
            connectedExits: 'Соединенные выходы и путешествие',
            otherLocations: 'Другие известные локации',
            travelTo: 'Перейти в',
            objectsInScene: 'Интерактивные объекты и окружение',
            searchRoom: 'Тщательно обыскать всю область на тайники и двери',
            inspect: 'Осмотреть',
            interact: 'Взаимодействовать',
            regenerateMap: 'Перегенерировать карту',
            targetInAction: 'Выбрать целью в действии',
            tacticalMenuTitle: 'Тактические действия',
            closeMenu: 'Закрыть меню',
            cellActions: {
                moveCarefully: 'Осторожно подойти',
                moveCarefullyDesc: 'Скрытно подойти, высматривая ловушки и засады',
                sprintDash: 'Совершить рывок (бег)',
                sprintDashDesc: 'Быстро преодолеть дистанцию на полной скорости',
                exploreSearch: 'Осмотреть место',
                exploreSearchDesc: 'Изучить тайники, руны, следы и окружение',
                takeCover: 'Занять укрытие',
                takeCoverDesc: 'Занять защитную позицию и подготовить оборону',
                aimTarget: 'Прицелиться в зону',
                aimTargetDesc: 'Подготовить дистанционную атаку или заклинание',
            },
            objectActions: {
                interact: 'Взаимодействовать',
                interactDesc: 'Активировать или задействовать объект',
                inspect: 'Осмотреть механизм',
                inspectDesc: 'Проверить на ловушки, надписи и секреты',
                openSearch: 'Открыть и обыскать',
                openSearchDesc: 'Вскрыть и проверить содержимое',
                forceBreak: 'Взломать силой',
                forceBreakDesc: 'Попытаться разбить или выбить объект',
                useCover: 'Укрыться за объектом',
                useCoverDesc: 'Использовать объект как тактическое укрытие',
            },
            characterActions: {
                meleeAttack: 'Атака в ближнем бою',
                meleeAttackDesc: 'Сблизиться и ударить оружием ближнего боя',
                rangedAttack: 'Дистанционная атака',
                rangedAttackDesc: 'Выстрелить из лука или метнуть снаряд',
                castSpell: 'Сотворить заклинание',
                castSpellDesc: 'Направить боевое заклинание на цель',
                assessThreat: 'Оценить угрозу',
                assessThreatDesc: 'Изучить защиту, повадки и слабости противника',
                intimidate: 'Угрожать / Переговоры',
                intimidateDesc: 'Потребовать сложить оружие или сдаться',
                speak: 'Поговорить',
                speakDesc: 'Начать разговор или передать сведения',
                assist: 'Помочь (Help)',
                assistDesc: 'Оказать содействие соратнику в бою',
                healAid: 'Исцелить / Помощь',
                healAidDesc: 'Оказать первую помощь или перевязать раны',
                defend: 'Защитить щитом',
                defendDesc: 'Прикрыть союзника своим щитом и телом',
                dodge: 'Уклонение (Dodge)',
                dodgeDesc: 'Сфокусироваться на защите и избегании атак',
                disengage: 'Аккуратный отход',
                disengageDesc: 'Выйти из ближнего боя без провоцированной атаки',
                survey: 'Оценить обстановку',
                surveyDesc: 'Перевести дух и осмотреть всю арену боя',
            },
        },
        character: {
            heroTab: 'Герой',
            itemsTab: 'Снаряжение',
            abilitiesTab: 'Способности',
            partyTab: 'Отряд',
            hp: 'Здоровье (HP)',
            ac: 'Класс доспеха (AC)',
            speed: 'Скорость',
            level: 'Уровень',
            str: 'СИЛ',
            dex: 'ЛОВ',
            con: 'ТЕЛ',
            int: 'ИНТ',
            wis: 'МДР',
            cha: 'ХАР',
            equip: 'Экипировать',
            unequip: 'Снять',
            drop: 'Бросить',
            transfer: 'Передать',
            useAbility: 'Применить',
            emptyParty: 'Нет активного героя',
            selectHeroPrompt: 'Выберите персонажа из отряда для просмотра характеристик.',
        },
        dice: {
            title: 'Бросок кубиков (D&D 5e)',
            roll: 'Бросить',
            advantage: 'Преимущество',
            disadvantage: 'Помеха',
            normal: 'Обычный',
            history: 'История бросков',
        },
        languageSelector: {
            title: 'Глобальный язык',
            current: 'Язык',
            ruLabel: 'RU Русский',
            enLabel: 'EN English',
            tooltip: 'Глобальный язык интерфейса, Мастера (DM) и персонажей',
        },
    },
    en: {
        nav: {
            campaigns: 'Campaigns',
            lobby: 'Guild Hall',
            profile: 'Profile',
            logout: 'Log Out',
            adventurer: 'Adventurer',
            backToCampaigns: '← Back to Campaigns',
        },
        auth: {
            title: 'MAGGxDND',
            subtitle: 'AI-Powered D&D Tactical Engine & Chronicle',
            guestHeading: 'Quick Guest Entry',
            enterAsGuest: 'Enter as Guest',
            enterTheRealm: 'Enter the Realm',
            username: 'Adventurer Name / Username',
            usernamePlaceholder: 'e.g. Thorgrim Ironfoot',
            password: 'Password',
            passwordPlaceholder: 'Enter your password',
            switchPassword: 'Use persistent account',
            switchGuest: 'Quick guest access',
            switchRegister: 'Create new account',
            switchLogin: 'Already registered? Sign In',
            register: 'Create Account',
            login: 'Sign In',
            connecting: 'Opening the gates...',
            errorFillBoth: 'Please provide both username and password.',
        },
        lobby: {
            title: 'Guild Hall & Active Campaigns',
            subtitle: 'Choose an active journey or forge a new quest',
            createAdventure: 'Forge Adventure',
            activeCampaigns: 'Active Campaigns',
            quickPresets: 'Preset Adventure Hooks',
            noCampaigns: 'No active campaigns found. Forge the first one!',
            modalTitle: 'Forge a New Campaign',
            campaignName: 'Campaign Name',
            campaignNamePlaceholder: 'e.g. Secrets of the Forgotten Crypt',
            scenePrompt: 'Starting Scene & Atmosphere',
            scenePromptPlaceholder: 'Describe the starting scene (tavern, dungeon, ancient ruins...)',
            gameLanguage: 'Game Language (DM, Story & Characters)',
            russian: 'Russian (RU)',
            english: 'English (EN)',
            forgeBtn: 'Forge Adventure',
            forging: 'Weaving realm...',
            cancelBtn: 'Cancel',
            enterCampaign: 'Enter Campaign',
            playersCount: 'Players',
        },
        sessionLobby: {
            headline: 'Party Gathering & Hero Selection',
            activeSession: 'Active Session',
            claimPrompt: 'Select an adventurer to claim control or roll a new hero. AI pilots unoccupied companions.',
            rollNewHero: 'Roll New Hero',
            closeForm: '✕ Close Form',
            heroName: 'Hero Name',
            heroNamePlaceholder: 'e.g. Katherine Stormwind',
            heroClass: 'Class',
            heroRace: 'Race',
            rollHeroBtn: 'Roll Hero & Enter Dungeon',
            claimHero: 'Claim Hero',
            claimedByYou: 'Piloted by you',
            aiControlled: 'AI Controlled',
            occupiedBy: 'Claimed by',
            enterGame: 'Enter Dungeon',
            partyRoster: 'Party Roster',
        },
        game: {
            storyFocus: 'Story Focus',
            splitView: 'Split View',
            mapFocus: 'Map Focus',
            dmThinking: 'DM is weaving reality...',
            heroCodex: 'Hero Codex',
            currentChapter: 'Current Chapter',
            objectives: 'Objectives',
            viewQuests: '▼ View Quests',
            hideQuests: '▲ Hide',
            nextObjective: 'Next Objective',
            allCompleted: 'All Chapter Objectives Completed! 🎉',
            completed: 'COMPLETED',
            modeStory: 'STORY',
            modeCombat: 'COMBAT',
            connecting: 'Connecting...',
            connected: 'Live',
            enterCombatTooltip: 'Switch into turn-based combat mode',
            exitCombatTooltip: 'Conclude combat and return to story mode',
            sceneDossier: 'Scene Dossier & Environment',
            questsTooltip: 'Active chapter progression & quests',
            diceRollerTooltip: 'D&D 5e Tactical Dice Roller',
        },
        chat: {
            storyFilter: 'Story & Dialogue',
            storyEventsFilter: 'Story + System Events',
            allFilter: 'Full Chronicle',
            rollsFilter: 'Dice Rolls Only',
            dmFilter: 'DM Rulings Only',
            inputPlaceholder: 'Describe your action, speech, or intention... (Enter to act)',
            actButton: 'Act',
            resolving: 'Resolving...',
            fastCommands: 'Fast Actions',
            clarifyPrompt: 'Dungeon Master requests clarification:',
            actions: {
                attack: 'Attack',
                attackDesc: 'Strike nearest hostile target',
                attackPrompt: 'I make a weapon attack against the nearest hostile target.',
                dash: 'Dash',
                dashDesc: 'Double movement speed this turn',
                dashPrompt: 'I take the Dash action to gain extra movement for this turn.',
                dodge: 'Dodge',
                dodgeDesc: 'Disadvantage on attacks against you',
                dodgePrompt: 'I take the Dodge action, focusing entirely on evading incoming attacks.',
                hide: 'Hide',
                hideDesc: 'Stealth check for cover',
                hidePrompt: 'I attempt to hide behind available cover with a Dexterity (Stealth) check.',
                search: 'Search',
                searchDesc: 'Inspect surroundings for traps and clues',
                searchPrompt: 'I carefully search my surroundings with an Investigation / Perception check.',
                help: 'Help Ally',
                helpDesc: 'Aid friendly creature with advantage',
                helpPrompt: 'I use the Help action to give advantage to my ally on their next check or attack.',
                interact: 'Use Object',
                interactDesc: 'Operate mechanism or object in the scene',
                interactPrompt: 'I interact with the nearest object or mechanism in the scene.',
                speak: 'Dialogue',
                speakDesc: 'Converse with party or NPCs',
                speakPrompt: 'I speak aloud: "',
            },
        },
        scene: {
            dossier: 'Tactical Dossier',
            arena: 'Arena',
            environment: 'Environment & Narrative',
            connectedExits: 'Connected Exits & Travel',
            otherLocations: 'Other Visited Locations',
            travelTo: 'Travel to',
            objectsInScene: 'Interactive Objects & Props',
            searchRoom: 'Search entire area for hidden doors and loot',
            inspect: 'Inspect',
            interact: 'Interact',
            regenerateMap: 'Regenerate Map',
            targetInAction: 'Target in Action',
            tacticalMenuTitle: 'Tactical Actions',
            closeMenu: 'Close Menu',
            cellActions: {
                moveCarefully: 'Move Carefully',
                moveCarefullyDesc: 'Advance stealthily, watching for traps and ambushes',
                sprintDash: 'Sprint / Dash',
                sprintDashDesc: 'Move at full speed to this position',
                exploreSearch: 'Explore & Search',
                exploreSearchDesc: 'Inspect ground, walls, and surroundings for secrets or hazards',
                takeCover: 'Take Cover',
                takeCoverDesc: 'Take a defensive stance and guard this position',
                aimTarget: 'Target Area',
                aimTargetDesc: 'Prepare a ranged attack or spell targeting this grid coordinate',
            },
            objectActions: {
                interact: 'Interact',
                interactDesc: 'Use or activate this object',
                inspect: 'Inspect & Examine',
                inspectDesc: 'Check for secret compartments, runes, or mechanisms',
                openSearch: 'Open & Search',
                openSearchDesc: 'Open and search contents for items or treasure',
                forceBreak: 'Force / Break',
                forceBreakDesc: 'Attempt to break open or destroy this object using force',
                useCover: 'Use as Cover',
                useCoverDesc: 'Take cover behind this object from incoming attacks',
            },
            characterActions: {
                meleeAttack: 'Melee Attack',
                meleeAttackDesc: 'Advance and strike in close-quarters melee combat',
                rangedAttack: 'Ranged Attack',
                rangedAttackDesc: 'Attack from a distance with bow or thrown weapon',
                castSpell: 'Cast Spell',
                castSpellDesc: 'Target with an offensive or tactical spell',
                assessThreat: 'Assess Threat',
                assessThreatDesc: 'Analyze defenses, weaknesses, and intentions',
                intimidate: 'Intimidate / Parley',
                intimidateDesc: 'Demand they yield, drop weapons, or negotiate',
                speak: 'Speak & Converse',
                speakDesc: 'Converse, share tactical information, or confer',
                assist: 'Assist (Help Action)',
                assistDesc: 'Grant advantage to this ally on their next action',
                healAid: 'Heal / First Aid',
                healAidDesc: 'Tend to injuries with medicine or healing abilities',
                defend: 'Defend & Guard',
                defendDesc: 'Position yourself to intercept attacks meant for this ally',
                dodge: 'Dodge Action',
                dodgeDesc: 'Focus entirely on defense until next turn',
                disengage: 'Disengage',
                disengageDesc: 'Move freely without provoking opportunity attacks',
                survey: 'Survey Field',
                surveyDesc: 'Scan the entire arena for tactical advantages',
            },
        },
        character: {
            heroTab: 'Hero',
            itemsTab: 'Items',
            abilitiesTab: 'Spells',
            partyTab: 'Party',
            hp: 'Hit Points (HP)',
            ac: 'Armor Class (AC)',
            speed: 'Speed',
            level: 'Level',
            str: 'STR',
            dex: 'DEX',
            con: 'CON',
            int: 'INT',
            wis: 'WIS',
            cha: 'CHA',
            equip: 'Equip',
            unequip: 'Unequip',
            drop: 'Drop',
            transfer: 'Transfer',
            useAbility: 'Cast / Use',
            emptyParty: 'No Active Hero Selected',
            selectHeroPrompt: 'Select an adventurer from the party list to view their character sheet.',
        },
        dice: {
            title: 'Dice Roller (D&D 5e)',
            roll: 'Roll',
            advantage: 'Advantage',
            disadvantage: 'Disadvantage',
            normal: 'Normal',
            history: 'Roll History',
        },
        languageSelector: {
            title: 'Global Language',
            current: 'Language',
            ruLabel: 'RU Russian',
            enLabel: 'EN English',
            tooltip: 'Global language for UI, Dungeon Master (DM), and characters',
        },
    },
};
