import os
import unittest
from unittest.mock import patch

from dev_settings import COINS_ENV
from game_state import GameState


class GameStateDevGunTests(unittest.TestCase):
    def test_default_gun_is_the_first_owned_gun_and_still_needs_selection(self):
        state = GameState()

        self.assertEqual(state.selected_gun, "pistol")
        self.assertTrue(state.needs_gun_selection())

    def test_dev_gun_can_be_selected_without_ownership(self):
        state = GameState(dev_gun="machine_gun")

        self.assertEqual(state.selected_gun, "machine_gun")
        self.assertFalse(state.owns_gun("machine_gun"))
        self.assertFalse(state.needs_gun_selection())

    def test_dev_gun_skips_the_selection_screen(self):
        state = GameState(owned_guns=["pistol", "rifle"], dev_gun="rifle")

        self.assertFalse(state.needs_gun_selection())

    def test_coins_can_come_from_the_environment(self):
        with patch.dict(os.environ, {COINS_ENV: "12345"}):
            state = GameState()

        self.assertEqual(state.coins, 12345)

    def test_explicit_coins_override_the_environment(self):
        with patch.dict(os.environ, {COINS_ENV: "12345"}):
            state = GameState(coins=7)

        self.assertEqual(state.coins, 7)

    def test_normal_ownership_still_requires_selection(self):
        state = GameState(owned_guns=["pistol", "rifle"])

        self.assertTrue(state.needs_gun_selection())


if __name__ == "__main__":
    unittest.main()
