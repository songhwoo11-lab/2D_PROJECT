import unittest

from game_state import GameState


class GameStateDevGunTests(unittest.TestCase):
    def test_default_gun_is_the_first_owned_gun(self):
        state = GameState()

        self.assertEqual(state.selected_gun, "pistol")
        self.assertFalse(state.needs_gun_selection())

    def test_dev_gun_can_be_selected_without_ownership(self):
        state = GameState(dev_gun="machine_gun")

        self.assertEqual(state.selected_gun, "machine_gun")
        self.assertFalse(state.owns_gun("machine_gun"))
        self.assertFalse(state.needs_gun_selection())

    def test_dev_gun_skips_the_selection_screen(self):
        state = GameState(owned_guns=["pistol", "rifle"], dev_gun="rifle")

        self.assertFalse(state.needs_gun_selection())

    def test_normal_ownership_still_requires_selection(self):
        state = GameState(owned_guns=["pistol", "rifle"])

        self.assertTrue(state.needs_gun_selection())


if __name__ == "__main__":
    unittest.main()
