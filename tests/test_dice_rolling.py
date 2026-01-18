import unittest
import sys
sys.path.append('D:\\Duty\\MAGGxDND')
from magg.magg import roll_dice, roll

class TestDiceRolling(unittest.TestCase):

    def test_roll_dice_valid_notation(self):
        self.assertTrue(1 <= roll_dice("1d4") <= 4)
        self.assertTrue(1 <= roll_dice("1d6") <= 6)
        self.assertTrue(1 <= roll_dice("1d8") <= 8)
        self.assertTrue(1 <= roll_dice("1d10") <= 10)
        self.assertTrue(1 <= roll_dice("1d12") <= 12)
        self.assertTrue(1 <= roll_dice("1d20") <= 20)
        self.assertTrue(1 <= roll_dice("1d100") <= 100)
        self.assertTrue(-1 <= roll_dice("1d4-2") <= 2)  # Test with negative modifier
        self.assertTrue(3 <= roll_dice("1d4+2") <= 6)   # Test with positive modifier
        self.assertTrue(2 <= roll_dice("2d4") <= 8)   # Test with multiple dice

    def test_roll_dice_default_num_dice(self):
        self.assertTrue(1 <= roll_dice("d6") <= 6)

    def test_roll_dice_invalid_notation(self):
        with self.assertRaises(ValueError):
            roll_dice("invalid")
        with self.assertRaises(ValueError):
            roll_dice("1d3")
        with self.assertRaises(ValueError):
            roll_dice("1d101")

    def test_roll_valid_expression(self):
        self.assertTrue(4 <= roll("2d6+1") <= 13)
        self.assertTrue(0 <= roll("1d20-1") <= 19)
        self.assertTrue(1 <= roll("d8") <= 8)
        self.assertTrue(6 <= roll("2d6+3-1d4+2") <= 17)
        self.assertTrue(2 <= roll("1+1") <= 2)  # simple addition

    def test_roll_with_whitespace(self):
        self.assertTrue(4 <= roll("2d6 + 1") <= 13)
        self.assertTrue(0 <= roll("1d20 - 1") <= 19)
        self.assertTrue(1 <= roll("  d8  ") <= 8)
        self.assertTrue(6 <= roll("2d6 + 3 - 1d4 + 2") <= 17)
        self.assertTrue(2 <= roll("+ 1 + 1") <= 2)  # simple addition


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
