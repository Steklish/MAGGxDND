import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { highlightNarrativeKeywords } from './keywordHighlighter';

describe('keywordHighlighter', () => {
    it('preserves full Russian DM narrative without dropping any words or characters', () => {
        const russianText =
            'Холодный воздух Обсидиановой Крепости пропитывает каждый камень, когда бродяга пытается обнажить клинок, но пальцы нащупывают лишь пустоту — оружие словно растворилось в тени забытых залов. Рядом замерли спутники: женщина в чешуйчатых доспехах со святым символом и воин с пламенным сердцем, чье дыхание вырывается облачками пара в мрачной тишине.';

        const rendered = render(<div>{highlightNarrativeKeywords(russianText)}</div>);
        // The full text content must match the original text verbatim
        expect(rendered.container.textContent).toBe(russianText);

        // Keywords like 'Обсидиановой Крепости', 'клинок', 'оружие', 'залов', 'доспехах', 'воин' should be highlighted
        const entityTags = rendered.container.querySelectorAll('.kw-tag.kw-entity');
        const locationTags = rendered.container.querySelectorAll('.kw-tag.kw-location');
        const itemTags = rendered.container.querySelectorAll('.kw-tag.kw-item');

        expect(entityTags.length).toBeGreaterThan(0);
        expect(locationTags.length).toBeGreaterThan(0);
        expect(itemTags.length).toBeGreaterThan(0);
    });

    it('highlights English D&D keywords and dice rolls accurately while preserving text', () => {
        const englishText =
            'A fierce goblin ambushes from the dark dungeon chamber, slashing with a poisoned dagger for 1d6+2 piercing damage! DC 14 check required.';

        const rendered = render(<div>{highlightNarrativeKeywords(englishText)}</div>);
        expect(rendered.container.textContent).toBe(englishText);

        const diceTags = rendered.container.querySelectorAll('.kw-tag.kw-dice');
        const entityTags = rendered.container.querySelectorAll('.kw-tag.kw-entity');
        const locationTags = rendered.container.querySelectorAll('.kw-tag.kw-location');
        const itemTags = rendered.container.querySelectorAll('.kw-tag.kw-item');

        expect(diceTags.length).toBeGreaterThanOrEqual(1);
        expect(entityTags.length).toBeGreaterThanOrEqual(1);
        expect(locationTags.length).toBeGreaterThanOrEqual(1);
        expect(itemTags.length).toBeGreaterThanOrEqual(1);
    });

    it('supports custom dynamic entity names from party and NPCs', () => {
        const text = 'Valeros and Nora Sunsword advance towards the altar.';
        const customEntities = ['Valeros', 'Nora Sunsword'];

        const rendered = render(<div>{highlightNarrativeKeywords(text, customEntities)}</div>);
        expect(rendered.container.textContent).toBe(text);

        const entityTags = rendered.container.querySelectorAll('.kw-tag.kw-entity');
        const texts = Array.from(entityTags).map(el => el.textContent);

        expect(texts).toContain('Valeros');
        expect(texts).toContain('Nora Sunsword');
    });

    it('handles markdown bold formatted text', () => {
        const text = 'The DM announces: **Critical Hit** on the **dragon**!';
        const rendered = render(<div>{highlightNarrativeKeywords(text)}</div>);
        expect(rendered.container.textContent).toBe('The DM announces: Critical Hit on the dragon!');

        const tags = rendered.container.querySelectorAll('.kw-tag');
        expect(tags.length).toBe(2);
    });
});
