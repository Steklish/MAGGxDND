import React from 'react';

export type KeywordClass = 'entity' | 'location' | 'item' | 'action' | 'dice';

interface KeywordRule {
    cls: KeywordClass;
    regex: RegExp;
    categoryTitle: string;
}

const ENTITY_WORDS = [
    // English
    'goblin', 'goblins', 'orc', 'orcs', 'dragon', 'dragons', 'skeleton', 'skeletons',
    'bandit', 'bandits', 'guard', 'guards', 'troll', 'trolls', 'beholder', 'lich',
    'wolf', 'wolves', 'beast', 'beasts', 'demon', 'demons', 'fiend', 'fiends',
    'cultist', 'cultists', 'kobold', 'kobolds', 'knight', 'knights', 'king', 'queen',
    'necromancer', 'sorcerer', 'wizard', 'assassin', 'wraith', 'ghoul', 'ghouls',
    'zombie', 'zombies', 'spider', 'spiders', 'giant', 'giants', 'dwarf', 'elf', 'tiefling',
    'cleric', 'rogue', 'fighter', 'bard', 'paladin', 'monk', 'druid', 'ranger', 'warlock', 'barbarian',
    'hero', 'heroes', 'adventurer', 'adventurers', 'companion', 'companions',
    // Russian
    'гоблин', 'гоблины', 'гоблинов', 'орк', 'орки', 'орков', 'дракон', 'драконы', 'дракона', 'драконов',
    'скелет', 'скелеты', 'скелетов', 'бандит', 'бандиты', 'бандитов', 'страж', 'стражи', 'стражей',
    'стражник', 'стражники', 'стражников', 'тролль', 'тролли', 'троллей', 'бехолдер', 'лич',
    'волк', 'волки', 'волков', 'зверь', 'звери', 'зверей', 'демон', 'демоны', 'демонов',
    'культист', 'культисты', 'культистов', 'кобольд', 'кобольды', 'кобольдов', 'рыцарь', 'рыцари', 'рыцарей',
    'король', 'королева', 'некромант', 'некроманты', 'чародей', 'чародеи', 'маг', 'маги',
    'волшебник', 'волшебники', 'ассасин', 'убийца', 'убийцы', 'призрак', 'призраки',
    'вурдалак', 'вурдалаки', 'зомби', 'паук', 'пауки', 'пауков', 'великан', 'великаны', 'великанов',
    'гном', 'гномы', 'дварф', 'дварфы', 'эльф', 'эльфы', 'тифлинг', 'тифлинги',
    'спутник', 'спутники', 'спутников', 'спутницы', 'клирик', 'клирики', 'плут', 'плуты',
    'бард', 'барды', 'паладин', 'паладины', 'друид', 'друиды', 'монах', 'монахи',
    'следопыт', 'следопыты', 'колдун', 'колдуны', 'варвар', 'варвары', 'бродяга', 'бродяги',
    'воин', 'воины', 'воинов', 'герой', 'герои', 'героев'
];

const LOCATION_WORDS = [
    // English
    'dungeon', 'dungeons', 'tavern', 'taverns', 'crypt', 'crypts', 'chamber', 'chambers',
    'cavern', 'caverns', 'cave', 'caves', 'hallway', 'corridor', 'corridors',
    'temple', 'temples', 'shrine', 'shrines', 'altar', 'altars', 'portal', 'portals',
    'gate', 'gates', 'bridge', 'bridges', 'throne', 'castle', 'castles',
    'fortress', 'fortresses', 'tower', 'towers', 'forest', 'forests', 'swamp', 'swamps',
    'catacomb', 'catacombs', 'sanctuary', 'cellar', 'cellars', 'ruins', 'vault', 'vaults',
    'room', 'rooms', 'door', 'doors', 'hall', 'halls', 'keep', 'citadel', 'sanctum',
    // Russian
    'подземелье', 'подземелья', 'подземелий', 'таверна', 'таверны', 'таверне', 'таверну',
    'крипта', 'крипты', 'крипте', 'крипту', 'покои', 'покоях', 'пещера', 'пещеры', 'пещере', 'пещеру',
    'коридор', 'коридоры', 'коридоре', 'коридорах', 'храм', 'храма', 'храме', 'храмы',
    'алтарь', 'алтаря', 'алтаре', 'портал', 'портала', 'портале', 'порталы', 'врата', 'ворота',
    'мост', 'моста', 'мосту', 'трон', 'тронный', 'замок', 'замка', 'замке',
    'крепость', 'крепости', 'крепостью', 'башня', 'башни', 'башне', 'башен',
    'лес', 'леса', 'лесу', 'болото', 'болота', 'болоте', 'катакомбы', 'катакомбах',
    'святилище', 'святилища', 'подвал', 'подвала', 'подвале', 'руины', 'руин', 'руинах',
    'хранилище', 'хранилища', 'комната', 'комнаты', 'комнате', 'комнату',
    'дверь', 'двери', 'дверью', 'дверям', 'зал', 'зала', 'зале', 'залов', 'залы',
    'цитадель', 'цитадели', 'цитаделью'
];

const ITEM_WORDS = [
    // English
    'sword', 'swords', 'blade', 'blades', 'shield', 'shields', 'dagger', 'daggers',
    'bow', 'bows', 'crossbow', 'crossbows', 'axe', 'axes', 'staff', 'staves',
    'wand', 'wands', 'potion', 'potions', 'elixir', 'elixirs', 'key', 'keys',
    'chest', 'chests', 'coffer', 'coffers', 'scroll', 'scrolls', 'tome', 'tomes',
    'book', 'books', 'ring', 'rings', 'amulet', 'amulets', 'relic', 'relics',
    'armor', 'armors', 'plate', 'chainmail', 'helmet', 'helmets', 'gold',
    'coins', 'coin', 'gem', 'gems', 'torch', 'torches', 'crate', 'crates',
    'barrel', 'barrels', 'lockpick', 'lockpicks', 'artifact', 'artifacts', 'weapon', 'weapons',
    // Russian
    'меч', 'меча', 'мечом', 'мечи', 'мечей', 'клинок', 'клинка', 'клинком', 'клинки', 'клинков',
    'щит', 'щита', 'щитом', 'щиты', 'щитов', 'кинжал', 'кинжала', 'кинжалом', 'кинжалы', 'кинжалов',
    'лук', 'лука', 'луком', 'арбалет', 'топор', 'топора', 'топором', 'топоры',
    'посох', 'посоха', 'посохом', 'жезл', 'жезла', 'зелье', 'зелья', 'зельем', 'зелий',
    'эликсир', 'эликсиры', 'эликсиром', 'ключ', 'ключа', 'ключом', 'ключи', 'ключей',
    'сундук', 'сундука', 'сундуком', 'сундуки', 'сундуков', 'свиток', 'свитка', 'свитком', 'свитки', 'свитков',
    'гримуар', 'книга', 'книги', 'книгой', 'кольцо', 'кольца', 'кольцом',
    'амулет', 'амулета', 'амулетом', 'амулеты', 'реликвия', 'реликвии', 'реликвию',
    'доспех', 'доспехи', 'доспехах', 'доспехами', 'кольчуга', 'кольчугу', 'латы',
    'шлем', 'шлема', 'золото', 'золота', 'монета', 'монеты', 'монет', 'монетами',
    'самоцвет', 'самоцветы', 'факел', 'факелы', 'факелом', 'отмычка', 'отмычки',
    'артефакт', 'артефакты', 'оружие', 'оружия', 'оружием'
];

const ACTION_WORDS = [
    // English
    'attack', 'attacks', 'strike', 'strikes', 'dash', 'dodge', 'disengage', 'hide',
    'cast', 'spell', 'spells', 'cantrip', 'cantrips', 'saving throw', 'skill check',
    'investigation', 'perception', 'stealth', 'athletics', 'acrobatics', 'initiative',
    'critical hit', 'critical miss', 'advantage', 'disadvantage', 'resistance', 'vulnerability',
    'stunned', 'poisoned', 'charmed', 'blinded', 'paralyzed', 'unconscious', 'restrained',
    'healing', 'rest',
    // Russian
    'атака', 'атаки', 'атаковать', 'атакует', 'удар', 'удары', 'нанести удар', 'обнажить',
    'рывок', 'уклонение', 'отход', 'скрытность', 'спрятаться',
    'заклинание', 'заклинания', 'заклинанием', 'заговор', 'заговоры',
    'спасбросок', 'спасброска', 'проверка', 'проверки', 'расследование', 'анализ',
    'внимательность', 'атлетика', 'акробатика', 'инициатива', 'инициативу',
    'критический удар', 'критический промах', 'преимущество', 'преимуществом',
    'помеха', 'помехой', 'сопротивление', 'уязвимость',
    'оглушен', 'оглушена', 'отравлен', 'отравлена', 'очарован', 'очарована',
    'ослеплен', 'ослеплена', 'парализован', 'парализована', 'без сознания',
    'связан', 'связана', 'исцеление', 'отдых'
];

function escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildWordPattern(words: string[]): string {
    const sorted = [...words].sort((a, b) => b.length - a.length);
    const escaped = sorted.map(escapeRegex).join('|');
    return `(?<![\\p{L}\\p{N}_])(?:${escaped})(?![\\p{L}\\p{N}_])`;
}

const DICE_PATTERN = '(?<![\\p{L}\\p{N}_])(?:\\d+d\\d+(?:\\s*[+-]\\s*\\d+)?|DC\\s*\\d+|AC\\s*\\d+|\\d+\\s*HP|\\d+\\s*(?:slashing|piercing|bludgeoning|fire|cold|lightning|radiant|necrotic|poison|acid|psychic|force)\\s*damage|СЛ\\s*\\d+|КД\\s*\\d+|\\d+\\s*(?:ХП|ОЗ)|\\d+\\s*(?:рубящего|колющего|дробящего|огненного|холодного|электрического|лучистого|некротического|ядовитого|кислотного|психического|силового)\\s*урона)(?![\\p{L}\\p{N}_])';

const ENTITY_PATTERN = buildWordPattern(ENTITY_WORDS);
const LOCATION_PATTERN = buildWordPattern(LOCATION_WORDS);
const ITEM_PATTERN = buildWordPattern(ITEM_WORDS);
const ACTION_PATTERN = buildWordPattern(ACTION_WORDS);

const DICE_REGEX = new RegExp(DICE_PATTERN, 'iu');
const ENTITY_REGEX = new RegExp(ENTITY_PATTERN, 'iu');
const LOCATION_REGEX = new RegExp(LOCATION_PATTERN, 'iu');
const ITEM_REGEX = new RegExp(ITEM_PATTERN, 'iu');
const ACTION_REGEX = new RegExp(ACTION_PATTERN, 'iu');

const RULES: KeywordRule[] = [
    { cls: 'dice', regex: DICE_REGEX, categoryTitle: 'Tactical Roll & Damage' },
    { cls: 'entity', regex: ENTITY_REGEX, categoryTitle: 'Entity / Foe' },
    { cls: 'location', regex: LOCATION_REGEX, categoryTitle: 'Location & Environment' },
    { cls: 'item', regex: ITEM_REGEX, categoryTitle: 'Item & Relic' },
    { cls: 'action', regex: ACTION_REGEX, categoryTitle: 'Combat & Action Rule' },
];

/**
 * Parses markdown bold (**keyword**) and categorized domain keywords
 * into structured stylized tags with hover labels and classes.
 * Safely preserves all Unicode characters (Cyrillic, symbols, whitespace, punctuation).
 */
export function highlightNarrativeKeywords(text: string, customEntities: string[] = []): React.ReactNode {
    if (!text || typeof text !== 'string') return text;

    // Filter and build dynamic custom entity regex if any are provided
    const validCustom = customEntities.filter(e => typeof e === 'string' && e.trim().length > 1);
    const dynamicPattern = validCustom.length > 0 ? buildWordPattern(validCustom) : null;
    const dynamicEntityRegex = dynamicPattern ? new RegExp(dynamicPattern, 'iu') : null;

    // Build the master regex for splitting plain text chunks
    const allPatterns: string[] = [DICE_PATTERN];
    if (dynamicPattern) {
        allPatterns.push(dynamicPattern);
    }
    allPatterns.push(ENTITY_PATTERN, LOCATION_PATTERN, ITEM_PATTERN, ACTION_PATTERN);

    const masterRegex = new RegExp(`(${allPatterns.join('|')})`, 'giu');

    // Tokenize by markdown bold first: **bold text**
    const boldParts = text.split(/(\*\*[^*]+\*\*)/g);

    return boldParts.map((part, pIdx) => {
        if (!part) return null;

        if (part.startsWith('**') && part.endsWith('**')) {
            const inner = part.slice(2, -2);
            let matchedClass: KeywordClass = 'entity';
            let title = 'Highlighted Keyword';

            if (dynamicEntityRegex && dynamicEntityRegex.test(inner)) {
                matchedClass = 'entity';
                title = 'Character / NPC';
            } else {
                for (const r of RULES) {
                    if (r.regex.test(inner)) {
                        matchedClass = r.cls;
                        title = r.categoryTitle;
                        break;
                    }
                }
            }

            return (
                <span
                    key={`b-${pIdx}`}
                    className={`kw-tag kw-${matchedClass}`}
                    title={`${title}: ${inner}`}
                >
                    {inner}
                </span>
            );
        }

        // Split plain chunk using master regex; all non-keyword and keyword tokens are preserved
        const tokens = part.split(masterRegex);

        return tokens.map((token, tIdx) => {
            if (!token) return null;

            // 1. Dynamic Entities (e.g. Current Character / NPC names)
            if (dynamicEntityRegex && dynamicEntityRegex.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-entity"
                        title={`Character / NPC: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            // 2. Tactical dice / damage
            if (DICE_REGEX.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-dice"
                        title={`Tactical Roll & Damage: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            // 3. Static domain rules
            if (ENTITY_REGEX.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-entity"
                        title={`Entity / Foe: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            if (LOCATION_REGEX.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-location"
                        title={`Location & Environment: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            if (ITEM_REGEX.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-item"
                        title={`Item & Relic: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            if (ACTION_REGEX.test(token)) {
                return (
                    <span
                        key={`p-${pIdx}-${tIdx}`}
                        className="kw-tag kw-action"
                        title={`Combat & Action Rule: ${token}`}
                    >
                        {token}
                    </span>
                );
            }

            return token;
        });
    });
}
