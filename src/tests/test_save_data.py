import tempfile
import unittest
from pathlib import Path

from save_data import BestLog, SaveData, default_save_data
from save_io import (
    SaveDataError,
    read_guns,
    read_upgrade_levels,
    write_guns,
    write_upgrade_levels,
)
from save_paths import (
    BEST_LOG_PATH,
    COINS_PATH,
    GAMEFILE_DIR,
    GUNS_PATH,
    RECENT_LOG_PATH,
    TRAINING_LOG_PATH,
    UPGRADE_PATH,
    ensure_gamefile_directories,
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

    def test_each_call_returns_independent_lists(self):
        first = default_save_data()
        second = default_save_data()

        first.acquired_guns[0] = False
        first.recent_logs.append((3, 10.0))

        self.assertTrue(second.acquired_guns[0])
        self.assertEqual(second.recent_logs, [])

    def test_best_log_stores_wave_and_time(self):
        log = BestLog(reached_wave=30, elapsed_time=125.5)

        self.assertEqual(log.reached_wave, 30)
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

