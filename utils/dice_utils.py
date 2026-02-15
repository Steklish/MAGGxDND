import re
import random

def roll_single_dice(dice_notation: str) -> int:
    """
    Parses a single dice term (e.g., '2d6', ' d 20 ', '2 D 6') and rolls it.
    Does NOT handle modifiers like '+3' (use roll() for that).
    """
    # Normalize: lowercase and remove spaces
    clean_notation = dice_notation.lower().replace(" ", "")

    # Regex to find 'count' and 'sides' (e.g., 2d6 or d20)
    # ^(\d*) matches the optional count (group 1)
    # d matches the letter d
    # (\d+|%)$ matches the sides (group 2), allows digits or '%' for d100
    pattern = re.compile(r'^(\d*)d(\d+|%)$')
    match = pattern.match(clean_notation)

    if not match:
        raise ValueError(f"Invalid single dice notation: '{dice_notation}'")

    # Group 1: Count (empty string means 1)
    count_str = match.group(1)
    num_dice = int(count_str) if count_str else 1

    # Group 2: Sides (handle % as 100)
    sides_str = match.group(2)
    dice_sides = 100 if sides_str == '%' else int(sides_str)

    # Optional: Keep the DnD validation check, or comment out to allow custom dice (d3, d50, etc)
    valid_sides = [4, 6, 8, 10, 12, 20, 100]
    if dice_sides not in valid_sides:
        # We assume standard DnD dice, but you can remove this block to allow any side count
        raise ValueError(f"Invalid dice type: d{dice_sides}. Allowed: {valid_sides}")

    total = 0
    for _ in range(num_dice):
        total += random.randint(1, dice_sides)

    return total


def roll_dice(expression: str) -> int:
    """
    Rolls dice based on a complex expression.
    Robustly handles messy inputs like: '2 d6 + 3', 'd20 - 1', '2D4+d6'.
    """
    # 1. Normalize input (lowercase)
    expression = expression.lower()

    # 2. Tokenize the string
    # This regex looks for two types of tokens preceded by an optional sign:
    # A: Dice notation --> ([+-]?) \s* (\d*) \s* d \s* (\d+|%)
    # B: Flat Modifiers -> ([+-]?) \s* (\d+)
    token_pattern = re.compile(r'([+-]?)\s*(?:(\d*)\s*d\s*(\d+|%)|(\d+))')

    total = 0
    
    # finditer finds all non-overlapping matches in the string
    matches = list(token_pattern.finditer(expression))
    
    if not matches:
        return 0

    for match in matches:
        sign_str = match.group(1)   # The + or - sign
        count_str = match.group(2)  # Dice count (e.g., '2' in 2d6)
        sides_str = match.group(3)  # Dice sides (e.g., '6' in 2d6)
        mod_str = match.group(4)    # Flat modifier (e.g., '3' in +3)

        # Determine multiplier based on sign (+1 or -1)
        multiplier = -1 if sign_str == '-' else 1

        if sides_str:
            # It is a Die (e.g., 2d6)
            # Reconstruct a clean string for roll_single_dice to handle
            # Use '1' if count is missing (e.g., d6 -> 1d6)
            c = count_str if count_str else "1"
            clean_dice_str = f"{c}d{sides_str}"
            
            # Roll it and add/subtract from total
            total += (roll_single_dice(clean_dice_str) * multiplier)
            
        elif mod_str:
            # It is a Modifier (e.g., 5)
            total += (int(mod_str) * multiplier)

    return total