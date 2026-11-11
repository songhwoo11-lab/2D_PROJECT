import unittest

from hp_trail import HpTrail


class HpTrailTests(unittest.TestCase):
    def test_starts_at_the_full_ratio(self):
        trail = HpTrail(100, 100)

        self.assertEqual(trail.value, 100)
        self.assertEqual(trail.ratio, 1.0)

    def test_damage_keeps_the_trailing_value_during_the_delay(self):
        trail = HpTrail(100, 100)

        trail.update(70, 0.1)

        self.assertEqual(trail.value, 100)

    def test_trailing_value_drains_after_the_delay(self):
        trail = HpTrail(100, 100, delay=0.3, full_drain_seconds=1.0)
        trail.update(70, 0.0)

        trail.update(70, 0.3)
        trail.update(70, 0.1)

        self.assertAlmostEqual(trail.value, 90.0)

    def test_trailing_value_stops_at_the_current_hp(self):
        trail = HpTrail(100, 100, delay=0.0, full_drain_seconds=1.0)
        trail.update(70, 0.0)

        trail.update(70, 10.0)

        self.assertEqual(trail.value, 70)
        self.assertEqual(trail.ratio, 0.7)

    def test_a_new_hit_restarts_the_delay(self):
        trail = HpTrail(100, 100, delay=0.3, full_drain_seconds=1.0)
        trail.update(70, 0.0)
        trail.update(70, 0.3)
        trail.update(70, 0.1)
        self.assertLess(trail.value, 100)

        trail.update(50, 0.0)
        drained = trail.value

        trail.update(50, 0.2)

        self.assertEqual(trail.value, drained)

    def test_healing_snaps_the_trailing_value(self):
        trail = HpTrail(100, 100)
        trail.update(70, 0.0)

        trail.update(85, 0.0)

        self.assertEqual(trail.value, 85)

    def test_reset_snaps_the_trailing_value_and_updates_the_maximum(self):
        trail = HpTrail(100, 100)
        trail.update(50, 0.0)

        trail.reset(150, 150)

        self.assertEqual(trail.value, 150)
        self.assertEqual(trail.max_hp, 150)

    def test_negative_delta_time_is_rejected(self):
        trail = HpTrail(100, 100)

        with self.assertRaises(ValueError):
            trail.update(100, -0.1)

    def test_non_finite_delta_time_is_rejected(self):
        trail = HpTrail(100, 100)

        with self.assertRaises(ValueError):
            trail.update(100, float("nan"))

    def test_non_positive_max_hp_is_rejected(self):
        with self.assertRaises(ValueError):
            HpTrail(0, 0)


if __name__ == "__main__":
    unittest.main()
