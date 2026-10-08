"""
backend/src/services/prompt_builder.py

Thematic prompt engineering builder for character portraits, item cards,
atmospheric scene headers, and orthographic top-down tactical battle maps.
"""
from typing import Optional, List, Tuple


class PromptBuilder:
    """Constructs prompt and negative prompt pairs tuned for fantasy RPG aesthetics."""

    @staticmethod
    def build_character_prompt(
        name: str,
        race: str,
        char_class: str,
        appearance: Optional[str] = None,
        backstory: Optional[str] = None,
        personality: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Bust / waist-up fantasy character portrait."""
        app_text = f"Appearance details: {str(appearance).strip()}. " if appearance else ""
        back_text = f"Background flavor: {str(backstory).strip()[:150]}. " if backstory else ""
        pers_items = [str(p) for p in personality[:3] if p] if personality else []
        pers_text = f"Personality traits: {', '.join(pers_items)}. " if pers_items else ""
        eq_items = [str(e) for e in equipment[:3] if e] if equipment else []
        eq_text = f"Equipment: {', '.join(eq_items)}. " if eq_items else ""

        prompt = (
            f"High fantasy digital art concept portrait of {name}, a {race} {char_class}. "
            f"{app_text}{back_text}{pers_text}{eq_text}"
            "Composition: Centered waist-up character portrait, 3/4 heroic angle, expressive countenance, "
            "dramatic cinematic rim lighting, textured garments and armor, soft moody atmospheric background with faint particles. "
            "Masterpiece fantasy illustration, 8k resolution, oil painting feel, artstation trending."
        )

        negative = (
            "modern clothing, guns, sunglasses, watches, digital screens, contemporary items, "
            "watermark, signature, text, logo, border, frames, deformed face, bad eyes, extra fingers, "
            "mutated hands, missing limbs, blurry, low quality, pixelated, 3d plastic render, anime, childish"
        )
        return prompt, negative

    @staticmethod
    def build_item_prompt(
        name: str,
        obj_type: Optional[str] = None,
        description: Optional[str] = None,
        damage_dice: Optional[str] = None,
        damage_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Solitary fantasy item equipment card."""
        type_str = obj_type or "equipment artifact"
        desc_text = f"Description: {str(description).strip()[:150]}. " if description else ""
        combat_text = f"Deals {damage_dice} {damage_type} damage. " if damage_dice else ""
        tag_items = [str(t) for t in tags[:3] if t] if tags else []
        magic_text = f"Enchanted properties: {', '.join(tag_items)}. " if tag_items else ""

        prompt = (
            f"Fantasy tabletop RPG item illustration of '{name}', a {type_str}. "
            f"{desc_text}{combat_text}{magic_text}"
            "Composition: Centered single object showcase, studio rim lighting, dark textured stone and aged parchment backdrop, "
            "intricate craftsmanship, finely detailed materials (gleaming steel, weathered leather, glowing runes, brass filigree), "
            "subtle magical aura particles. Tabletop asset art, sharp focus, 8k render."
        )

        negative = (
            "human character, hands holding object, fingers, people, person, face, multiple items, "
            "cluttered desk, background room, text, letters, interface, health bar, numbers, watermark, "
            "frames, borders, blurry, low resolution, simplistic cartoon"
        )
        return prompt, negative

    @staticmethod
    def build_scene_prompt(
        name: str,
        description: Optional[str] = "",
        environment_type: Optional[str] = None,
        mood: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Widescreen panoramic narrative scene header."""
        env_str = environment_type or "fantasy realm"
        mood_str = mood or "mysterious and evocative"
        desc_str = (description or "").strip()
        setting_text = f"Setting: {desc_str}. " if desc_str else ""

        prompt = (
            f"Cinematic wide-angle fantasy environment landscape: '{name}'. "
            f"{setting_text}"
            f"Environment type: {env_str}. Mood: {mood_str}. "
            "Composition: Panoramic 16:9 narrative establishing shot, deep atmospheric perspective, "
            "volumetric god rays, atmospheric mist, environmental storytelling, dramatic cinematic lighting, "
            "rich natural and architectural textures. Concept art masterpiece, Unreal Engine 5 render style, 8k resolution."
        )

        negative = (
            "close-up character faces, people dominating foreground, modern technology, wires, cars, "
            "modern buildings, text, titles, UI overlay, speech bubbles, split screen, collage, comic book paneling, "
            "blurry, washed out, low contrast"
        )
        return prompt, negative

    @staticmethod
    def build_battlemap_prompt(
        name: str,
        description: Optional[str] = "",
        dimensions: Tuple[int, int] = (20, 20),
        terrain_type: Optional[str] = None,
        obstacles: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Flat 2D orthographic aerial tactical battle map."""
        dim_x, dim_y = dimensions
        terrain_str = terrain_type or "stone dungeon floor and cobblestone"
        obs_items = [str(o) for o in obstacles[:5] if o] if obstacles else []
        obs_str = f"Static environmental obstacles: {', '.join(obs_items)}. " if obs_items else "Walls, pillars, rubble, and natural cover. "
        desc_str = (description or "").strip()
        desc_text = f"Description: {desc_str}. " if desc_str else ""

        prompt = (
            "Tactical tabletop RPG battle map, strictly flat 2D orthographic aerial top-down perspective (90 degrees overhead). "
            f"Location: '{name}'. Terrain: {terrain_str}. Arena dimensions: {dim_x} by {dim_y} grid units. "
            f"{desc_text}{obs_str}"
            "Texture: Highly detailed ground textures, distinct elevation edges, clean spatial floor plan. "
            "Strict camera layout: Perfectly perpendicular overhead bird's-eye view. "
            "Pristine game map canvas ready for digital token overlay."
        )

        negative = (
            "isometric, angled perspective, 3D tilt, side view, eye-level, first person, third person, "
            "characters, player tokens, monsters, creatures, miniatures, people, figurines, "
            "grid lines, square grid overlay, hex grid lines, ruler marks, printed grid, "
            "text, map legend, compass rose, numbers, UI, borders, frame, blurry textures"
        )
        return prompt, negative
