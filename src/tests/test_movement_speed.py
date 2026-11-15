import math
import unittest

from arrow import Arrow
from bullet import Bullet
from enemy import ENEMY_STATS, Enemy, EnemyType
from game_config import (
    ARROW_SPEED,
    BULLET_SPEED,
    KMH_TO_PIXELS_PER_SECOND,
    PIXELS_PER_METER,
    PLAYER_SPEED,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from player import Player


ENEMY_SPEED_KMH = {
    EnemyType.BASIC: 10.0,
    EnemyType.EXPLOSIVE: 12.0,
    EnemyType.TANKER: 5.0,
    EnemyType.ARCHER: 8.0,
    EnemyType.ASSASSIN: 15.0,
}


def to_kmh(pixels_per_second):
    return pixels_per_second / PIXELS_PER_METER * 3.6


class SpeedConversionTests(unittest.TestCase):
    def test_distance_scale_is_sixty_pixels_per_meter(self):
        self.assertEqual(PIXELS_PER_METER, 60)

    def test_conversion_factor_matches_sixty_pixels_per_meter(self):
        self.assertAlmostEqual(
            KMH_TO_PIXELS_PER_SECOND,
            1000 / 3600 * 60,
        )

    def test_player_speed_is_twenty_kmh(self):
        self.assertAlmostEqual(to_kmh(PLAYER_SPEED), 20.0)

    def test_bullet_speed_is_one_hundred_kmh(self):
        self.assertAlmostEqual(to_kmh(BULLET_SPEED), 100.0)

    def test_arrow_speed_is_seventy_five_kmh(self):
        self.assertAlmostEqual(to_kmh(ARROW_SPEED), 75.0)

    def test_enemy_speeds_match_the_requested_kmh_values(self):
        for enemy_type, expected_kmh in ENEMY_SPEED_KMH.items():
            with self.subTest(enemy_type=enemy_type):
                self.assertAlmostEqual(
                    to_kmh(ENEMY_STATS[enemy_type].move_speed),
                    expected_kmh,
                )


class SpeedApplicationTests(unittest.TestCase):
    def test_player_moves_at_its_configured_speed(self):
        player = Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
        player.set_movement(1.0, 0.0)

        player.update(1.0)

        self.assertAlmostEqual(
            player.x,
            WORLD_WIDTH / 2 + PLAYER_SPEED,
        )

    def test_basic_enemy_moves_at_its_configured_speed(self):
        player = Player(2000.0, 2000.0)
        enemy = Enemy(
            0.0,
            0.0,
            ENEMY_STATS[EnemyType.BASIC],
            player=player,
        )

        enemy.update(1.0)

        self.assertAlmostEqual(
            math.hypot(enemy.x, enemy.y),
            ENEMY_STATS[EnemyType.BASIC].move_speed,
        )

    def test_bullet_moves_at_its_configured_speed(self):
        start_x = WORLD_WIDTH / 2
        start_y = WORLD_HEIGHT / 2
        bullet = Bullet(start_x, start_y, 0.0, None)

        bullet.update(0.1)

        self.assertAlmostEqual(bullet.x - start_x, BULLET_SPEED * 0.1)

    def test_arrow_moves_at_its_configured_speed(self):
        start_x = WORLD_WIDTH / 2
        start_y = WORLD_HEIGHT / 2
        arrow = Arrow(
            start_x,
            start_y,
            start_x + 10000.0,
            start_y,
            None,
        )

        arrow.update(0.1)

        self.assertAlmostEqual(arrow.x - start_x, ARROW_SPEED * 0.1)
