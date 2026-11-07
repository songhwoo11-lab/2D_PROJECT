import unittest

from shot_result import HitResult, damage_for_result, resolve_hit_roll


class ShotResultTests(unittest.TestCase):
    def test_roll_boundaries_match_prd_probabilities(self):
        self.assertIs(resolve_hit_roll(0.0), HitResult.HEADSHOT)
        self.assertIs(resolve_hit_roll(0.0099), HitResult.HEADSHOT)
        self.assertIs(resolve_hit_roll(0.01), HitResult.MISS)
        self.assertIs(resolve_hit_roll(0.0999), HitResult.MISS)
        self.assertIs(resolve_hit_roll(0.10), HitResult.HIT)

    def test_roll_outside_unit_interval_is_rejected(self):
        for value in (-0.01, 1.0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "range"):
                    resolve_hit_roll(value)

    def test_damage_matches_hit_result(self):
        self.assertEqual(damage_for_result(5, HitResult.HEADSHOT), 15)
        self.assertEqual(damage_for_result(5, HitResult.MISS), 0)
        self.assertEqual(damage_for_result(5, HitResult.HIT), 5)


if __name__ == "__main__":
    unittest.main()
