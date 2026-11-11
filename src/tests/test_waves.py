import random
import unittest
from collections import Counter

from enemy import EnemyType
from game_config import TOTAL_WAVES
from waves import (
    SPAWN_RADIUS_RANGES,
    WaveDirector,
    build_wave_spawn_order,
    random_spawn_position,
    spawn_radius_range,
    validate_wave,
    wave_composition,
    wave_enemy_count,
    wave_stat_multiplier,
)


class WaveCompositionTests(unittest.TestCase):
    def test_first_wave_is_all_basic_enemies(self):
        self.assertEqual(wave_enemy_count(1), 10)
        self.assertEqual(wave_composition(1), {EnemyType.BASIC: 10})

    def test_second_wave_adds_archers(self):
        composition = wave_composition(2)

        self.assertEqual(wave_enemy_count(2), 20)
        self.assertEqual(composition[EnemyType.BASIC], 18)
        self.assertEqual(composition[EnemyType.ARCHER], 2)

    def test_tenth_wave_has_one_hundred_enemies(self):
        composition = wave_composition(10)

        self.assertEqual(wave_enemy_count(10), 100)
        for enemy_type in EnemyType:
            self.assertEqual(composition[enemy_type], 20)

    def test_every_wave_spawns_ten_enemies_per_wave_number(self):
        for wave in range(1, TOTAL_WAVES + 1):
            self.assertEqual(
                wave_enemy_count(wave),
                wave * 10,
                msg="wave {}".format(wave),
            )

    def test_ratios_repeat_every_ten_waves(self):
        def ratios(wave):
            composition = wave_composition(wave)
            total = sum(composition.values())
            return {
                enemy_type: count / total
                for enemy_type, count in composition.items()
            }

        for offset in range(10):
            self.assertEqual(
                ratios(1 + offset),
                ratios(11 + offset),
                msg="wave {} vs {}".format(1 + offset, 11 + offset),
            )
            self.assertEqual(
                ratios(1 + offset),
                ratios(21 + offset),
                msg="wave {} vs {}".format(1 + offset, 21 + offset),
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
        self.assertEqual(director.total_to_spawn, 10)
        self.assertEqual(director.spawned_count, 0)
        self.assertFalse(director.all_spawned)

    def test_spawns_fifty_enemies_per_second(self):
        director = WaveDirector(random_source=random.Random(0))
        for _ in range(9):
            director.advance()

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

        self.assertEqual(spawned, 10)
        self.assertTrue(director.all_spawned)

    def test_advance_loads_the_next_wave(self):
        director = WaveDirector(random_source=random.Random(0))

        self.assertTrue(director.advance())

        self.assertEqual(director.current_wave, 2)
        self.assertEqual(director.total_to_spawn, 20)
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


class SpawnRadiusTests(unittest.TestCase):
    def test_radius_ranges_match_the_product_requirements(self):
        self.assertEqual(SPAWN_RADIUS_RANGES[EnemyType.BASIC], (500.0, 1000.0))
        self.assertEqual(
            SPAWN_RADIUS_RANGES[EnemyType.EXPLOSIVE],
            (800.0, 1000.0),
        )
        self.assertEqual(SPAWN_RADIUS_RANGES[EnemyType.TANKER], (200.0, 500.0))
        self.assertEqual(
            SPAWN_RADIUS_RANGES[EnemyType.ASSASSIN],
            (200.0, 300.0),
        )
        self.assertEqual(SPAWN_RADIUS_RANGES[EnemyType.ARCHER], (600.0, 800.0))

    def test_assassin_spawns_within_its_radius_band(self):
        random_source = random.Random(7)
        player_x, player_y = 800.0, 600.0
        for _ in range(200):
            x, y = random_spawn_position(
                EnemyType.ASSASSIN,
                player_x,
                player_y,
                1600.0,
                1200.0,
                random_source,
            )
            distance = ((x - player_x) ** 2 + (y - player_y) ** 2) ** 0.5
            self.assertGreaterEqual(distance, 200.0 - 1e-9)
            self.assertLessEqual(distance, 300.0 + 1e-9)

    def test_spawn_positions_never_leave_the_map(self):
        random_source = random.Random(11)
        for enemy_type in EnemyType:
            for _ in range(100):
                x, y = random_spawn_position(
                    enemy_type,
                    200.0,
                    150.0,
                    1600.0,
                    1200.0,
                    random_source,
                )
                self.assertGreaterEqual(x, 0.0)
                self.assertLessEqual(x, 1600.0)
                self.assertGreaterEqual(y, 0.0)
                self.assertLessEqual(y, 1200.0)

    def test_unsupported_enemy_type_is_rejected(self):
        with self.assertRaises(ValueError):
            spawn_radius_range("basic")


if __name__ == "__main__":
    unittest.main()
