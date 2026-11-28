import os
import unittest
from unittest.mock import patch

from dev_settings import COINS_ENV
from game_config import DIFFICULTY_EASY, DIFFICULTY_HARD, DIFFICULTY_NORMAL
from game_state import GameState
from save_data import default_save_data


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

    def test_training_records_start_empty(self):
        self.assertEqual(GameState().training_records, [])

    def test_newest_training_record_is_added_first(self):
        from battle_record import TrainingRecord

        state = GameState()
        state.add_training_record(TrainingRecord(targets_destroyed=3))
        state.add_training_record(TrainingRecord(targets_destroyed=9))

        self.assertEqual(
            [record.targets_destroyed for record in state.training_records],
            [9, 3],
        )


class GameStateDifficultyTests(unittest.TestCase):
    def test_new_state_starts_on_normal(self):
        self.assertEqual(GameState().difficulty, DIFFICULTY_NORMAL)

    def test_set_difficulty_normalizes_and_updates_the_state(self):
        state = GameState()

        self.assertEqual(state.set_difficulty(" hard "), DIFFICULTY_HARD)
        self.assertEqual(state.difficulty, DIFFICULTY_HARD)

    def test_unknown_difficulty_is_rejected(self):
        state = GameState()

        with self.assertRaises(ValueError):
            state.set_difficulty("NIGHTMARE")

    def test_difficulty_round_trips_through_save_data(self):
        state = GameState()
        state.set_difficulty(DIFFICULTY_EASY)

        self.assertEqual(state.to_save_data().difficulty, DIFFICULTY_EASY)
        restored = GameState.from_save_data(state.to_save_data())
        self.assertEqual(restored.difficulty, DIFFICULTY_EASY)

    def test_from_save_data_uses_the_stored_difficulty(self):
        data = default_save_data()
        data.difficulty = DIFFICULTY_HARD

        self.assertEqual(GameState.from_save_data(data).difficulty, DIFFICULTY_HARD)


if __name__ == "__main__":
    unittest.main()
