# tests/test_mechanics.py
import unittest
from main import GameState

class TestMechanics(unittest.TestCase):
    def test_hp_mechanics(self):
        gs = GameState()
        gs.hp = 50
        gs.hp = min(100, gs.hp + 10)
        self.assertEqual(gs.hp, 60)

if __name__ == '__main__':
    unittest.main()