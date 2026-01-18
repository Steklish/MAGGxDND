import re
import random


def roll_dice(dice_notation: str) -> int:
    """Interprets DnD-like dice notation and returns the total sum of the dice rolls and modifiers.

    Args:
        dice_notation (str): A string representing the dice notation (e.g., '2d6+3', '1d20-1').

    Returns:
        int: The total sum of the dice rolls and modifiers.
    """
    # Regular expression to match dice notation (e.g., 2d6, 1d20, d8) and modifiers (+3, -1)
    pattern = re.compile(r'(\d*)d(\d+)([+-]\d+)?')

    match = pattern.match(dice_notation)

    if not match:
        raise ValueError("Invalid dice notation")

    num_dice = int(match.group(1)) if match.group(1) else 1  # Default to 1 if no number of dice is specified
    dice_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if dice_sides not in [4, 6, 8, 10, 12, 20, 100]:
        raise ValueError("Invalid dice type")

    total = 0
    for _ in range(num_dice):
        total += random.randint(1, dice_sides)

    total += modifier

    return total


def roll(expression: str) -> int:
    """Rolls dice based on the given expression, supporting multiple dice rolls and modifiers.

    Args:
        expression (str): A string representing the roll expression (e.g., '2d6+3', '1d20-1+1d4').

    Returns:
        int: The total sum of the dice rolls and modifiers.
    """
    total = 0
    # Split the expression into individual dice rolls and modifiers
    parts = re.findall(r'(\d*d\d+[+-]?\d*)|([+-]?\s*\d+)', expression)
    for part in parts:
        dice_notation, modifier = part
        if dice_notation:
            total += roll_dice(dice_notation)
        elif modifier:
            total += int(modifier.replace(" ", ""))  # Remove spaces and convert to integer

    return total

if __name__ == '__main__':
    # Example usage
    print(roll_dice("2d6+3"))  # Roll two d6 and add 3
    print(roll_dice("1d20-1")) # Roll one d20 and subtract 1
    print(roll_dice("d8"))    # Roll one d8

    print(roll("2d6+3"))  # Roll two d6 and add 3
    print(roll("1d20-1")) # Roll one d20 and subtract 1
    print(roll("d8"))    # Roll one d8
    print(roll("2d6+3-1d4+2")) # Roll two d6, add 3, subtract one d4, and add 2