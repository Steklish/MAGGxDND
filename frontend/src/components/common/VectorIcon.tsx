import React from 'react';
import './VectorIcon.css';

export const ICON_MAP = {
    // Combat & Weapons
    'sword': '/assets/vectors/sword-suit-svgrepo-com.svg',
    'swords': '/assets/vectors/sword-suit-svgrepo-com.svg',
    'broadsword': '/assets/vectors/broadsword-svgrepo-com.svg',
    'axe': '/assets/vectors/magic-axe-svgrepo-com.svg',
    'battleaxe': '/assets/vectors/magic-axe-svgrepo-com.svg',
    'halberd': '/assets/vectors/halberd-svgrepo-com.svg',
    'sharp-halberd': '/assets/vectors/sharp-halberd-svgrepo-com.svg',
    'trident': '/assets/vectors/magic-trident-svgrepo-com.svg',
    'magic-trident': '/assets/vectors/magic-trident-svgrepo-com.svg',

    // Shields & Defense
    'shield': '/assets/vectors/shield-medieval-svgrepo-com.svg',
    'shield-ornate': '/assets/vectors/shield-medieval-svgrepo-com (1).svg',
    'shield-round': '/assets/vectors/round-shield-svgrepo-com.svg',
    'shield-checked': '/assets/vectors/checked-shield-svgrepo-com.svg',
    'shield-warrior': '/assets/vectors/medieval-warrior-shield-svgrepo-com.svg',
    'shield-magic': '/assets/vectors/magic-shield-svgrepo-com.svg',

    // Armor & Gear
    'armor': '/assets/vectors/breastplate-svgrepo-com.svg',
    'breastplate': '/assets/vectors/breastplate-svgrepo-com.svg',
    'chest-armor': '/assets/vectors/chest-armor-svgrepo-com.svg',
    'helm': '/assets/vectors/closed-barbute-svgrepo-com.svg',
    'helmet': '/assets/vectors/closed-barbute-svgrepo-com.svg',
    'light-helm': '/assets/vectors/light-helm-svgrepo-com.svg',

    // Characters & Roles
    'knight': '/assets/vectors/medieval-knight-svgrepo-com.svg',
    'knight-helm': '/assets/vectors/knight-svgrepo-com.svg',
    'knight-spear': '/assets/vectors/knight-svgrepo-com (1).svg',
    'crusader': '/assets/vectors/crusader-svgrepo-com.svg',
    'paladin': '/assets/vectors/crusader-svgrepo-com.svg',
    'woman': '/assets/vectors/medieval-woman-svgrepo-com.svg',
    'hero': '/assets/vectors/medieval-knight-svgrepo-com.svg',
    'user': '/assets/vectors/knight-svgrepo-com.svg',
    'player': '/assets/vectors/knight-svgrepo-com.svg',

    // Castles, Locations & Places
    'castle': '/assets/vectors/medieval-castle-svgrepo-com.svg',
    'castle-simple': '/assets/vectors/castle-svgrepo-com.svg',
    'castle-gate': '/assets/vectors/castle-f-svgrepo-com.svg',
    'tower': '/assets/vectors/medieval-tower-svgrepo-com.svg',
    'tent': '/assets/vectors/medieval-tent-svgrepo-com.svg',
    'camp': '/assets/vectors/medieval-tent-svgrepo-com.svg',
    'lobby': '/assets/vectors/medieval-tent-svgrepo-com.svg',

    // Leadership & DM
    'crown': '/assets/vectors/medieval-crown-svgrepo-com.svg',
    'dm': '/assets/vectors/medieval-crown-svgrepo-com.svg',
    'master': '/assets/vectors/medieval-crown-svgrepo-com.svg',
    'king': '/assets/vectors/medieval-crown-svgrepo-com.svg',

    // Speed, Travel & Mount
    'horse': '/assets/vectors/warhorse-svgrepo-com.svg',
    'warhorse': '/assets/vectors/warhorse-svgrepo-com.svg',
    'mount': '/assets/vectors/warhorse-svgrepo-com.svg',
    'speed': '/assets/vectors/warhorse-svgrepo-com.svg',

    // Banners & Faction
    'banner': '/assets/vectors/knight-banner-svgrepo-com.svg',
    'flag': '/assets/vectors/knight-banner-svgrepo-com.svg',

    // Magic & Arcana
    'gate': '/assets/vectors/magic-gate-svgrepo-com.svg',
    'portal': '/assets/vectors/magic-gate-svgrepo-com.svg',
    'broom': '/assets/vectors/magic-broom-svgrepo-com.svg',
    'magic': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'spell': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'spells': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'swirl': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'magic-swirl': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'sparkle': '/assets/vectors/magic-swirl-svgrepo-com.svg',
    'potion': '/assets/vectors/magic-potion-svgrepo-com.svg',
    'flask': '/assets/vectors/magic-potion-svgrepo-com.svg',
    'item': '/assets/vectors/magic-potion-svgrepo-com.svg',
    'inventory': '/assets/vectors/magic-potion-svgrepo-com.svg',
    'cauldron': '/assets/vectors/magic-trick-1-svgrepo-com.svg',
    'pot': '/assets/vectors/magic-trick-1-svgrepo-com.svg',
    'wizard': '/assets/vectors/magic-trick-3-svgrepo-com.svg',
    'hat': '/assets/vectors/magic-trick-3-svgrepo-com.svg',
    'sorcerer': '/assets/vectors/magic-trick-3-svgrepo-com.svg',
    'rune-circle': '/assets/vectors/magic-square-1-svgrepo-com.svg',
    'rune-square': '/assets/vectors/magic-square-2-svgrepo-com.svg',
    'rune': '/assets/vectors/magic-square-3-svgrepo-com.svg',
    'dice': '/assets/vectors/magic-square-3-svgrepo-com.svg',
    'd20': '/assets/vectors/magic-square-3-svgrepo-com.svg',
    'seal': '/assets/vectors/magic-square-3-svgrepo-com.svg',
} as const;

export type IconName = keyof typeof ICON_MAP;

export interface VectorIconProps {
    name: IconName;
    className?: string;
    style?: React.CSSProperties;
    size?: number | string;
    color?: string;
    spin?: boolean;
    title?: string;
    ariaHidden?: boolean;
    onClick?: () => void;
}

export const VectorIcon: React.FC<VectorIconProps> = ({
    name,
    className = '',
    style,
    size,
    color,
    spin = false,
    title,
    ariaHidden = true,
    onClick,
}) => {
    const iconUrl = ICON_MAP[name] || ICON_MAP.sword;

    const customStyle: React.CSSProperties = {
        ...style,
        WebkitMaskImage: `url('${iconUrl}')`,
        maskImage: `url('${iconUrl}')`,
        ...(size !== undefined
            ? {
                  width: typeof size === 'number' ? `${size}px` : size,
                  height: typeof size === 'number' ? `${size}px` : size,
              }
            : {}),
        ...(color !== undefined ? { backgroundColor: color } : {}),
    };

    return (
        <span
            className={`vector-icon vector-icon--${name} ${spin ? 'vector-icon--spin' : ''} ${className}`}
            style={customStyle}
            aria-hidden={ariaHidden}
            title={title}
            onClick={onClick}
            role="img"
        />
    );
};

export default VectorIcon;
