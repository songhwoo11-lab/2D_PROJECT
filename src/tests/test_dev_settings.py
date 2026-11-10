import unittest

from dev_settings import (
    SPAWN_RATE_ENV,
    WAVES_ENV,
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


if __name__ == "__main__":
    unittest.main()
