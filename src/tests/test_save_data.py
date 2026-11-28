import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from battle_record import BattleRecord, VICTORY
from game_config import DIFFICULTY_EASY, DIFFICULTY_HARD, DIFFICULTY_NORMAL
from game_state import GameState
from save_data import (
    RECENT_LOG_LIMIT,
    BestLog,
    SaveData,
    default_save_data,
    limit_recent_logs,
    select_best_log,
)
from save_io import (
    SaveDataError,
    read_best_log,
    read_coins,
    read_difficulty,
    read_guns,
    read_recent_logs,
    read_training_records,
    read_upgrade_levels,
    load_save_data,
    load_save_data_with_report,
    write_best_log,
    write_coins,
    write_difficulty,
    write_guns,
    write_recent_logs,
    write_save_data,
    validate_save_data,
    write_training_records,
    write_upgrade_levels,
)
from save_paths import (
    BEST_LOG_PATH,
    COINS_PATH,
    DIFFICULTY_PATH,
    GAMEFILE_DIR,
    GUNS_PATH,
    RECENT_LOG_PATH,
    TRAINING_LOG_PATH,
    UPGRADE_PATH,
    ensure_gamefile_directories,
    gamefile_paths,
)
from shop import GUN_SHOP_ORDER


class DefaultSaveDataTests(unittest.TestCase):
    def test_only_the_first_gun_is_owned(self):
        data = default_save_data()

        self.assertEqual(len(data.acquired_guns), len(GUN_SHOP_ORDER))
        self.assertEqual(data.acquired_guns[0], True)
        self.assertEqual(data.acquired_guns[1:], [False] * (len(GUN_SHOP_ORDER) - 1))

    def test_every_gun_starts_at_level_zero(self):
        self.assertEqual(
            default_save_data().upgrade_levels, [0] * len(GUN_SHOP_ORDER)
        )

    def test_empty_progress_and_records(self):
        data = default_save_data()

        self.assertEqual(data.coins, 0)
        self.assertIsNone(data.best_log)
        self.assertEqual(data.recent_logs, [])
        self.assertEqual(data.training_records, [])

    def test_default_difficulty_is_normal(self):
        self.assertEqual(default_save_data().difficulty, DIFFICULTY_NORMAL)

    def test_each_call_returns_independent_lists(self):
        first = default_save_data()
        second = default_save_data()

        first.acquired_guns[0] = False
        first.recent_logs.append((3, 10.0))

        self.assertTrue(second.acquired_guns[0])
        self.assertEqual(second.recent_logs, [])

    def test_best_log_stores_wave_and_time(self):
        log = BestLog(reached_wave=10, elapsed_time=125.5)

        self.assertEqual(log.reached_wave, 10)
        self.assertEqual(log.elapsed_time, 125.5)

    def test_save_data_accepts_custom_values(self):
        data = SaveData(
            acquired_guns=[True],
            upgrade_levels=[2],
            coins=100,
            best_log=BestLog(10, 40.0),
            recent_logs=[(10, 40.0)],
            training_records=[7],
        )

        self.assertEqual(data.coins, 100)
        self.assertEqual(data.training_records, [7])


class GunFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "getGuns.txt"
            write_guns([True, False, True], path)

            self.assertEqual(read_guns(path), [True, False, True])

    def test_file_uses_the_prd_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "getGuns.txt"
            write_guns([True, False, False], path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(),
                "acquire = [true, false, false]",
            )

    def test_invalid_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "getGuns.txt"
            path.write_text("acquire = [yes, false]\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_guns(path)


class UpgradeFileTests(unittest.TestCase):
    def test_round_trip_keeps_internal_levels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "LvGuns.txt"
            write_upgrade_levels([0, 2, 10], path)

            self.assertEqual(read_upgrade_levels(path), [0, 2, 10])

    def test_default_levels_use_the_prd_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "LvGuns.txt"
            write_upgrade_levels([0, 0, 0], path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(),
                "gunLevel = [1, 1, 1]",
            )

    def test_stored_levels_outside_the_allowed_range_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "LvGuns.txt"
            path.write_text("gunLevel = [0, 1, 1]\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_upgrade_levels(path)


class CoinFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "coins.txt"
            write_coins(12345, path)

            self.assertEqual(read_coins(path), 12345)

    def test_file_uses_the_prd_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "coins.txt"
            write_coins(0, path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(), "coins = 0"
            )

    def test_negative_coins_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "coins.txt"
            path.write_text("coins = -1\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_coins(path)


class DifficultyFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "difficulty.txt"
            write_difficulty(DIFFICULTY_HARD, path)

            self.assertEqual(read_difficulty(path), DIFFICULTY_HARD)
            self.assertEqual(
                path.read_text(encoding="utf-8").strip(), "difficulty = HARD"
            )

    def test_lower_case_input_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "difficulty.txt"
            write_difficulty("easy", path)

            self.assertEqual(read_difficulty(path), DIFFICULTY_EASY)

    def test_unknown_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "difficulty.txt"
            path.write_text("difficulty = NIGHTMARE\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_difficulty(path)

    def test_invalid_format_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "difficulty.txt"
            path.write_text("difficulty HARD\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_difficulty(path)


class BestLogFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "BestLog.txt"
            write_best_log(BestLog(reached_wave=10, elapsed_time=125.5), path)

            loaded = read_best_log(path)
            self.assertEqual(loaded.reached_wave, 10)
            self.assertEqual(loaded.elapsed_time, 125.5)

    def test_missing_record_uses_zero_sentinel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "BestLog.txt"
            write_best_log(None, path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(), "BestLog = [0, 0]"
            )
            self.assertIsNone(read_best_log(path))

    def test_out_of_range_wave_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "BestLog.txt"
            path.write_text("BestLog = [31, 10]\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_best_log(path)


class RecentLogFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latelyLog.txt"
            write_recent_logs([(10, 60.0), (7, 125.5)], path)

            self.assertEqual(
                read_recent_logs(path), [(10, 60.0), (7, 125.5)]
            )

    def test_empty_log_uses_the_prd_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latelyLog.txt"
            write_recent_logs([], path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(), "log = []"
            )
            self.assertEqual(read_recent_logs(path), [])

    def test_malformed_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latelyLog.txt"
            path.write_text("log = [[10, 60], [oops]]\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_recent_logs(path)


class TrainingLogFileTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trainingLog.txt"
            write_training_records([12, 7, 0], path)

            self.assertEqual(read_training_records(path), [12, 7, 0])

    def test_file_uses_the_training_log_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trainingLog.txt"
            write_training_records([5], path)

            self.assertEqual(
                path.read_text(encoding="utf-8").strip(),
                "trainingLog = [5]",
            )

    def test_negative_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "trainingLog.txt"
            path.write_text("trainingLog = [-1]\n", encoding="utf-8")

            with self.assertRaises(SaveDataError):
                read_training_records(path)


class SaveDataValidationTests(unittest.TestCase):
    def test_default_data_is_valid(self):
        self.assertTrue(validate_save_data(default_save_data()))

    def test_missing_field_is_detected(self):
        data = default_save_data()
        del data.coins

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

    def test_wrong_list_length_is_detected(self):
        data = default_save_data()
        data.acquired_guns = [True]

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

    def test_wrong_value_types_are_detected(self):
        data = default_save_data()
        data.acquired_guns = [1, False, False]

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

        data = default_save_data()
        data.coins = True

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

    def test_out_of_range_best_log_is_detected(self):
        data = default_save_data()
        data.best_log = BestLog(reached_wave=99, elapsed_time=10.0)

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

    def test_invalid_difficulty_is_detected(self):
        data = default_save_data()
        data.difficulty = "NIGHTMARE"

        with self.assertRaises(SaveDataError):
            validate_save_data(data)

    def test_invalid_data_is_not_written(self):
        data = default_save_data()
        data.coins = -5
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(SaveDataError):
                write_save_data(data, temp_dir)

            self.assertFalse(gamefile_paths(temp_dir)["coins"].exists())

    def test_damaged_file_is_detected_on_load(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(default_save_data(), temp_dir)
            gamefile_paths(temp_dir)["guns"].write_text(
                "acquire = [true, maybe, false]\n", encoding="utf-8"
            )

            with self.assertRaises(SaveDataError):
                read_guns(gamefile_paths(temp_dir)["guns"])


class RecordRankingTests(unittest.TestCase):
    def test_higher_wave_wins_even_with_a_longer_time(self):
        best = select_best_log([(10, 900.0), (9, 100.0)])

        self.assertEqual(best, BestLog(reached_wave=10, elapsed_time=900.0))

    def test_equal_waves_use_the_shorter_time(self):
        best = select_best_log([(10, 300.0), (10, 250.0), (9, 10.0)])

        self.assertEqual(best, BestLog(reached_wave=10, elapsed_time=250.0))

    def test_best_log_objects_are_accepted(self):
        best = select_best_log(
            [BestLog(reached_wave=12, elapsed_time=90.0), (12, 80.0)]
        )

        self.assertEqual(best, BestLog(reached_wave=12, elapsed_time=80.0))

    def test_no_records_means_no_best_log(self):
        self.assertIsNone(select_best_log([]))

    def test_recent_logs_are_limited_to_ten(self):
        logs = [(wave, float(wave)) for wave in range(1, 21)]

        self.assertEqual(limit_recent_logs(logs), logs[:RECENT_LOG_LIMIT])

    def test_written_recent_logs_are_limited(self):
        data = default_save_data()
        data.recent_logs = [
            (wave, float(wave)) for wave in range(1, 11)
        ] + [(10, 10.0)]
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)

            self.assertEqual(
                read_recent_logs(gamefile_paths(temp_dir)["recent_logs"]),
                data.recent_logs[:RECENT_LOG_LIMIT],
            )


class GameStateSaveConversionTests(unittest.TestCase):
    def test_loaded_data_is_applied_to_live_state(self):
        data = SaveData(
            acquired_guns=[False, True, True],
            upgrade_levels=[0, 2, 10],
            coins=700,
            best_log=BestLog(reached_wave=10, elapsed_time=900.0),
            recent_logs=[(10, 900.0), (9, 100.0)],
            training_records=[5, 8],
        )

        with patch.dict(os.environ, {}, clear=True):
            state = GameState.from_save_data(data)

        self.assertEqual(state.owned_guns, ["rifle", "machine_gun"])
        self.assertEqual(state.upgrade_level("rifle"), 2)
        self.assertEqual(state.upgrade_level("machine_gun"), 10)
        self.assertEqual(state.coins, 700)
        self.assertEqual(state.selected_gun, "rifle")
        self.assertEqual([record.reached_wave for record in state.records], [10, 9])
        self.assertEqual(state.records[0].result, VICTORY)
        self.assertEqual(
            [record.targets_destroyed for record in state.training_records],
            [5, 8],
        )

    def test_best_record_rules_are_applied_when_saving(self):
        state = GameState(
            records=[
                BattleRecord("defeat", reached_wave=10, elapsed_time=30.0),
                BattleRecord("defeat", reached_wave=25, elapsed_time=500.0),
                BattleRecord("defeat", reached_wave=25, elapsed_time=450.0),
            ],
            best_log=BestLog(reached_wave=5, elapsed_time=20.0),
        )

        saved = state.to_save_data()

        self.assertEqual(
            saved.best_log, BestLog(reached_wave=25, elapsed_time=450.0)
        )

    def test_live_state_converts_back_to_save_data(self):
        data = SaveData(
            acquired_guns=[True, True, False],
            upgrade_levels=[0, 3, 0],
            coins=1250,
            best_log=BestLog(reached_wave=20, elapsed_time=400.0),
            recent_logs=[(20, 400.0), (9, 90.0)],
            training_records=[11],
        )
        with patch.dict(os.environ, {}, clear=True):
            state = GameState.from_save_data(data)

        restored = state.to_save_data()

        self.assertEqual(restored.acquired_guns, data.acquired_guns)
        self.assertEqual(restored.upgrade_levels, data.upgrade_levels)
        self.assertEqual(restored.coins, data.coins)
        self.assertEqual(restored.recent_logs, data.recent_logs)
        self.assertEqual(restored.training_records, data.training_records)


class SaveLoadRecoveryTests(unittest.TestCase):
    def test_missing_files_create_defaults_without_damage_recovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_save_data_with_report(temp_dir)

            self.assertFalse(result.recovered)
            self.assertEqual(result.data, default_save_data())
            self.assertTrue(result.messages)
            self.assertIn("기본값을 생성", result.guidance_text())
            self.assertTrue(result.guidance_text())

    def test_damaged_file_uses_default_and_keeps_the_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(default_save_data(), temp_dir)
            coins_path = gamefile_paths(temp_dir)["coins"]
            coins_path.write_text("coins = broken\n", encoding="utf-8")

            result = load_save_data_with_report(temp_dir)

            self.assertTrue(result.recovered)
            self.assertEqual(result.data.coins, 0)
            self.assertIn("coins.txt", result.guidance_text())
            self.assertEqual(
                coins_path.read_text(encoding="utf-8"), "coins = broken\n"
            )

    def test_invalid_combined_data_falls_back_to_all_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(default_save_data(), temp_dir)
            with patch(
                "save_io.validate_save_data",
                side_effect=SaveDataError("broken save"),
            ):
                result = load_save_data_with_report(temp_dir)

            self.assertTrue(result.recovered)
            self.assertEqual(result.data, default_save_data())
            self.assertIn("전체 기본값으로 복구", result.guidance_text())

    def test_load_save_data_still_returns_only_the_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(load_save_data(temp_dir), default_save_data())


class GameFileStoreTests(unittest.TestCase):
    def test_first_run_creates_all_default_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data = load_save_data(temp_dir)

            self.assertEqual(data, default_save_data())
            for path in gamefile_paths(temp_dir).values():
                self.assertTrue(path.exists(), path)

    def test_round_trip_every_file(self):
        data = SaveData(
            acquired_guns=[True, True, False],
            upgrade_levels=[0, 3, 10],
            coins=2500,
            best_log=BestLog(reached_wave=10, elapsed_time=305.25),
            recent_logs=[(10, 305.25), (9, 110.0)],
            training_records=[9, 14],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)

            self.assertEqual(load_save_data(temp_dir), data)

    def test_missing_files_are_filled_from_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            coins_path = gamefile_paths(temp_dir)["coins"]
            coins_path.parent.mkdir(parents=True, exist_ok=True)
            write_coins(500, coins_path)

            data = load_save_data(temp_dir)

            self.assertEqual(data.coins, 500)
            self.assertEqual(data.acquired_guns, default_save_data().acquired_guns)
            self.assertIsNone(data.best_log)
            self.assertEqual(data.training_records, [])
            for path in gamefile_paths(temp_dir).values():
                self.assertTrue(path.exists(), path)


class AtomicWriteTests(unittest.TestCase):
    def test_writes_through_a_temporary_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "getGuns.txt"
            original_replace = Path.replace
            replaced = []

            def spy_replace(self, target):
                replaced.append((self, target))
                return original_replace(self, target)

            with patch.object(Path, "replace", spy_replace):
                write_guns([True, False, False], path)

            self.assertEqual(len(replaced), 1)
            self.assertTrue(replaced[0][0].name.endswith(".tmp"))
            self.assertEqual(replaced[0][1], path)
            self.assertFalse(Path(temp_dir, "getGuns.txt.tmp").exists())

    def test_failed_replace_keeps_the_old_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "getGuns.txt"
            path.write_text("acquire = [true, true, true]\n", encoding="utf-8")

            with patch.object(Path, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(SaveDataError):
                    write_guns([False, False, False], path)

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "acquire = [true, true, true]\n",
            )
            self.assertFalse(Path(temp_dir, "getGuns.txt.tmp").exists())


class SavePathsTests(unittest.TestCase):
    def test_paths_follow_the_prd_layout(self):
        self.assertEqual(GUNS_PATH, GAMEFILE_DIR / "gun" / "getGuns.txt")
        self.assertEqual(UPGRADE_PATH, GAMEFILE_DIR / "gun" / "LvGuns.txt")
        self.assertEqual(COINS_PATH, GAMEFILE_DIR / "coin" / "coins.txt")
        self.assertEqual(
            BEST_LOG_PATH, GAMEFILE_DIR / "playlog" / "BestLog.txt"
        )
        self.assertEqual(
            RECENT_LOG_PATH, GAMEFILE_DIR / "playlog" / "latelyLog.txt"
        )
        self.assertEqual(
            TRAINING_LOG_PATH, GAMEFILE_DIR / "playlog" / "trainingLog.txt"
        )

    def test_directories_are_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = ensure_gamefile_directories(temp_dir)

            self.assertEqual(root, Path(temp_dir))
            for name in ("gun", "coin", "playlog"):
                self.assertTrue((Path(temp_dir) / name).is_dir())

    def test_gamefile_paths_accepts_a_custom_root(self):
        paths = gamefile_paths("custom")

        self.assertEqual(
            paths["training_records"],
            Path("custom") / "playlog" / "trainingLog.txt",
        )
        self.assertEqual(
            set(paths),
            {
                "guns",
                "upgrades",
                "coins",
                "best_log",
                "recent_logs",
                "training_records",
                "difficulty",
            },
        )

