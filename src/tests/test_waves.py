import random
import unittest
from collections import Counter

from enemy import EnemyType
from game_config import TOTAL_WAVES
from waves import (
    build_wave_spawn_order,
    validate_wave,
    wave_composition,
    wave_enemy_count,
)


class WaveCompositionTests(unittest.TestCase):
    def test_first_wave_is_all_basic_enemies(self):
        self.assertEqual(wave_enemy_count(1), 100)
        self.assertEqual(wave_composition(1), {EnemyType.BASIC: 100})

    def test_second_wave_adds_archers(self):
        composition = wave_composition(2)

        self.assertEqual(wave_enemy_count(2), 120)
        self.assertEqual(composition[EnemyType.BASIC], 108)
        self.assertEqual(composition[EnemyType.ARCHER], 12)

    def test_final_cycle_wave_has_500_enemies(self):
        composition = wave_composition(10)

        self.assertEqual(wave_enemy_count(10), 500)
        for enemy_type in EnemyType:
            self.assertEqual(composition[enemy_type], 100)

    def test_composition_repeats_every_ten_waves(self):
        for offset in range(10):
            self.assertEqual(
                wave_composition(1 + offset),
                wave_composition(11 + offset),
                msg="wave {} vs {}".format(1 + offset, 11 + offset),
            )

    def test_every_wave_composition_sums_to_its_count(self):
        for wave in range(1, TOTAL_WAVES + 1):
            composition = wave_composition(wave)
            self.assertEqual(
                sum(composition.values()),
                wave_enemy_count(wave),
                msg="wave {}".format(wave),
            )

    def test_composition_rejects_waves_outside_the_game(self):
        for invalid in (0, TOTAL_WAVES + 1, -1, "1"):
            with self.assertRaises(ValueError):
                validate_wave(invalid)


class SpawnOrderTests(unittest.TestCase):
    def test_spawn_order_contains_expected_enemy_types(self):
        order = build_wave_spawn_order(5)

        self.assertEqual(len(order), wave_enemy_count(5))
        self.assertEqual(Counter(order), Counter(wave_composition(5)))

    def test_shuffled_spawn_order_keeps_the_same_enemies(self):
        order = build_wave_spawn_order(8, random_source=random.Random(1234))

        self.assertEqual(len(order), wave_enemy_count(8))
        self.assertEqual(Counter(order), Counter(wave_composition(8)))


if __name__ == "__main__":
    unittest.main()
