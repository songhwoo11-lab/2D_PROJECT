import unittest

from dev_settings import (
    GUN_ENV,
    SPAWN_RATE_ENV,
    WAVES_ENV,
    development_gun,
    development_spawn_rate,
    development_total_waves,
)


class DevelopmentTotalWavesTests(unittest.TestCase):
    def test_missing_setting_uses_the_default(self):
        self.assertIsNone(development_total_waves({}))

    def test_positive_integer_overrides_the_wave_count(self):
        self.assertEqual(development_total_waves({WAVES_ENV: "3"}), 3)

    def test_invalid_values_are_ignored(self):
        for value in ("", "  ", "abc", "0", "-2", "2.5"):
            self.assertIsNone(
                development_total_waves({WAVES_ENV: value}),
                msg=repr(value),
            )


class DevelopmentSpawnRateTests(unittest.TestCase):
    def test_missing_setting_uses_the_default(self):
        self.assertIsNone(development_spawn_rate({}))

    def test_positive_rate_overrides_the_spawn_rate(self):
        self.assertEqual(
            development_spawn_rate({SPAWN_RATE_ENV: "200"}),
            200.0,
        )

    def test_invalid_values_are_ignored(self):
        for value in ("", "  ", "abc", "0", "-5"):
            self.assertIsNone(
                development_spawn_rate({SPAWN_RATE_ENV: value}),
                msg=repr(value),
            )


class DevelopmentGunTests(unittest.TestCase):
    def test_missing_setting_uses_the_default(self):
        self.assertIsNone(development_gun({}))

    def test_registered_gun_ids_are_accepted(self):
        self.assertEqual(development_gun({GUN_ENV: "rifle"}), "rifle")
        self.assertEqual(
            development_gun({GUN_ENV: "machine_gun"}),
            "machine_gun",
        )

    def test_gun_id_is_normalized(self):
        self.assertEqual(development_gun({GUN_ENV: " RIFLE "}), "rifle")

    def test_unknown_gun_ids_are_ignored(self):
        for value in ("", "  ", "unknown", "shotgun"):
            self.assertIsNone(development_gun({GUN_ENV: value}), msg=repr(value))


if __name__ == "__main__":
    unittest.main()
