import unittest

from spawn_warning import SpawnWarning


class SpawnWarningTests(unittest.TestCase):
    def test_new_warning_is_not_expired_and_has_no_progress(self):
        warning = SpawnWarning(10.0, 20.0, 16.0, duration=0.5)

        self.assertFalse(warning.is_expired)
        self.assertAlmostEqual(warning.progress, 0.0)

    def test_warning_expires_after_its_duration(self):
        warning = SpawnWarning(10.0, 20.0, 16.0, duration=0.5)

        warning.update(0.2)
        self.assertFalse(warning.is_expired)
        self.assertAlmostEqual(warning.progress, 0.4)
        warning.update(0.3)

        self.assertTrue(warning.is_expired)
        self.assertAlmostEqual(warning.progress, 1.0)

    def test_warning_does_not_shrink_below_zero(self):
        warning = SpawnWarning(0.0, 0.0, 10.0, duration=0.2)

        warning.update(5.0)

        self.assertEqual(warning.remaining, 0.0)
        self.assertTrue(warning.is_expired)

    def test_invalid_warning_values_are_rejected(self):
        with self.assertRaises(ValueError):
            SpawnWarning(0.0, 0.0, -1.0)
        with self.assertRaises(ValueError):
            SpawnWarning(0.0, 0.0, 10.0, duration=-1.0)
        warning = SpawnWarning(0.0, 0.0, 10.0)
        with self.assertRaises(ValueError):
            warning.update(-1.0)


if __name__ == "__main__":
    unittest.main()
