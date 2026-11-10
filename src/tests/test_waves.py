import random
import unittest
from collections import Counter

from enemy import EnemyType
from game_config import TOTAL_WAVES
from waves import (
    WaveDirector,
    build_wave_spawn_order,
    validate_wave,
    wave_composition,
    wave_enemy_count,
    wave_stat_multiplier,
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


class WaveStatMultiplierTests(unittest.TestCase):
    def test_first_block_uses_base_stats(self):
        self.assertEqual(wave_stat_multiplier(1), 1)
        self.assertEqual(wave_stat_multiplier(9), 1)

    def test_second_block_doubles_stats(self):
        self.assertEqual(wave_stat_multiplier(10), 2)
        self.assertEqual(wave_stat_multiplier(19), 2)

    def test_third_block_quadruples_stats(self):
        self.assertEqual(wave_stat_multiplier(20), 4)
        self.assertEqual(wave_stat_multiplier(29), 4)

    def test_final_wave_octuples_stats(self):
        self.assertEqual(wave_stat_multiplier(30), 8)


class WaveDirectorTests(unittest.TestCase):
    def test_starts_on_first_wave_with_full_queue(self):
        director = WaveDirector(random_source=random.Random(0))

        self.assertEqual(director.current_wave, 1)
        self.assertEqual(director.total_to_spawn, 100)
        self.assertEqual(director.spawned_count, 0)
        self.assertFalse(director.all_spawned)

    def test_spawns_fifty_enemies_per_second(self):
        director = WaveDirector(random_source=random.Random(0))

        spawned = sum(
            len(director.pending_spawns(1.0 / 60.0)) for _ in range(60)
        )

        self.assertEqual(spawned, 50)
        self.assertEqual(director.spawned_count, 50)

    def test_reports_all_spawned_after_the_queue_empties(self):
        director = WaveDirector(random_source=random.Random(0))
        spawned = 0
        while not director.all_spawned:
            spawned += len(director.pending_spawns(0.1))

        self.assertEqual(spawned, 100)
        self.assertTrue(director.all_spawned)

    def test_advance_loads_the_next_wave(self):
        director = WaveDirector(random_source=random.Random(0))

        self.assertTrue(director.advance())

        self.assertEqual(director.current_wave, 2)
        self.assertEqual(director.total_to_spawn, 120)
        self.assertEqual(director.spawned_count, 0)
        self.assertFalse(director.all_spawned)

    def test_cannot_advance_past_the_last_wave(self):
        director = WaveDirector(total_waves=2, random_source=random.Random(0))

        self.assertTrue(director.advance())
        self.assertFalse(director.advance())
        self.assertEqual(director.current_wave, 2)

    def test_rejects_invalid_configuration(self):
        with self.assertRaises(ValueError):
            WaveDirector(total_waves=0)
        with self.assertRaises(ValueError):
            WaveDirector(spawn_rate=0)


if __name__ == "__main__":
    unittest.main()
