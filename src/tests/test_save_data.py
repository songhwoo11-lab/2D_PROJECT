import unittest

from save_data import BestLog, SaveData, default_save_data
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
