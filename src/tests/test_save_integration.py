"""End-to-end checks for 8단계 save/load behaviour."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from battle_record import BattleRecord, TrainingRecord, VICTORY
from game_config import DIFFICULTY_EASY, DIFFICULTY_HARD, DIFFICULTY_NORMAL
from game_state import GameState
from save_data import (
    BestLog,
    RECENT_LOG_LIMIT,
    SaveData,
    default_save_data,
    empty_records_by_difficulty,
)
from save_io import load_save_data, load_save_data_with_report, write_save_data
from save_paths import gamefile_paths


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SaveIntegrationTests(unittest.TestCase):
    def test_first_run_creates_default_game_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_save_data_with_report(temp_dir)

            self.assertEqual(result.data, default_save_data())
            self.assertFalse(result.recovered)
            for path in gamefile_paths(temp_dir).values():
                self.assertTrue(path.exists(), path)

    def test_restart_round_trip_preserves_progress(self):
        data = SaveData(
            acquired_guns=[True, True, False],
            upgrade_levels=[0, 5, 10],
            coins=4321,
            best_log=BestLog(reached_wave=10, elapsed_time=1000.0),
            recent_logs=[(10, 1000.0), (9, 200.0)],
            training_records=[7, 9],
            difficulty=DIFFICULTY_HARD,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)
            reloaded = load_save_data(temp_dir)

            self.assertEqual(reloaded, data)
            with patch.dict(os.environ, {}, clear=True):
                state = GameState.from_save_data(reloaded)
                self.assertEqual(state.to_save_data(), data)

    def test_records_are_saved_separately_for_each_difficulty(self):
        data = default_save_data()
        data.records_by_difficulty = empty_records_by_difficulty()
        data.records_by_difficulty[DIFFICULTY_EASY] = [
            BattleRecord(
                "defeat",
                reached_wave=10,
                elapsed_time=210.5,
                clear_time=210.5,
                gun_id="rifle",
                cleared_wave=9,
                difficulty=DIFFICULTY_EASY,
            )
        ]
        data.records_by_difficulty[DIFFICULTY_HARD] = [
            BattleRecord(
                VICTORY,
                reached_wave=10,
                elapsed_time=880.0,
                clear_time=880.0,
                gun_id="pistol",
                cleared_wave=10,
                difficulty=DIFFICULTY_HARD,
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)
            paths = gamefile_paths(temp_dir)
            self.assertEqual(
                paths["records_EASY"].read_text(encoding="utf-8").strip(),
                "record = [[rifle, 9, 210.5]]",
            )
            self.assertEqual(
                paths["records_NORMAL"].read_text(encoding="utf-8").strip(),
                "record = []",
            )
            self.assertEqual(
                paths["records_HARD"].read_text(encoding="utf-8").strip(),
                "record = [[pistol, 10, 880]]",
            )

            reloaded = load_save_data(temp_dir)
            self.assertEqual(reloaded, data)
            with patch.dict(os.environ, {}, clear=True):
                state = GameState.from_save_data(reloaded)
            self.assertEqual(len(state.records_for_difficulty(DIFFICULTY_EASY)), 1)
            self.assertEqual(state.records_for_difficulty(DIFFICULTY_NORMAL), [])
            self.assertEqual(len(state.records_for_difficulty(DIFFICULTY_HARD)), 1)

    def test_damaged_save_is_recovered_with_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(default_save_data(), temp_dir)
            gamefile_paths(temp_dir)["guns"].write_text(
                "acquire = [true, false]\n", encoding="utf-8"
            )

            result = load_save_data_with_report(temp_dir)

            self.assertTrue(result.recovered)
            self.assertEqual(result.data, default_save_data())
            self.assertIn("getGuns.txt", result.guidance_text())

    def test_record_updates_keep_best_and_recent_limits(self):
        state = GameState(coins=50)
        state.add_record(BattleRecord(VICTORY, reached_wave=10, elapsed_time=1000.0))
        for wave in range(1, 11):
            state.add_record(
                BattleRecord("defeat", reached_wave=wave, elapsed_time=float(wave))
            )
        state.add_training_record(TrainingRecord(targets_destroyed=15))

        data = state.to_save_data()

        self.assertEqual(len(data.recent_logs), RECENT_LOG_LIMIT)
        self.assertEqual(data.best_log, BestLog(10, 10.0))
        self.assertEqual(data.training_records, [15])
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)

            self.assertEqual(load_save_data(temp_dir), data)

    def test_gamefile_directory_is_git_ignored(self):
        ignore_lines = [
            line.strip()
            for line in (PROJECT_ROOT / ".gitignore").read_text(
                encoding="utf-8"
            ).splitlines()
        ]

        self.assertIn("gamefile/", ignore_lines)
