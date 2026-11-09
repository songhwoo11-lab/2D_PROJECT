import math
import unittest
from unittest.mock import patch

import game_world
from bullet import Bullet
from game_config import BULLET_SIZE, WORLD_WIDTH
from enemy import ENEMY_STATS, Enemy, EnemyType
from shot_result import HitResult


class FakeImage:
    def __init__(self):
        self.rotate_calls = []

    def rotate_draw(self, *args):
        self.rotate_calls.append(args)


class BulletTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_bullet_moves_in_aim_direction(self):
        bullet = Bullet(100, 100, math.pi / 2, FakeImage(), speed=60)

        bullet.update()

        self.assertAlmostEqual(bullet.x, 100)
        self.assertAlmostEqual(bullet.y, 101)

    def test_bullet_draws_rotated_with_its_direction(self):
        image = FakeImage()
        bullet = Bullet(100, 200, math.pi / 2, image)
        bullet.set_screen_position(300, 400)

        bullet.draw()

        angle, x, y, width, height = image.rotate_calls[0]
        self.assertAlmostEqual(angle, math.pi / 4)
        self.assertEqual((x, y, width, height), (300, 400, BULLET_SIZE, BULLET_SIZE))

    def test_bullet_removes_itself_after_leaving_world(self):
        bullet = Bullet(WORLD_WIDTH - 1, 100, 0, FakeImage(), speed=120)
        game_world.add_object(bullet)

        bullet.update()

        self.assertNotIn(bullet, game_world.world[0])

    def test_bullet_detects_and_removes_on_enemy_collision(self):
        with patch("bullet.roll_hit_result", return_value=HitResult.HIT):
            enemy = Enemy(20, 100, ENEMY_STATS[EnemyType.BASIC])
            bullet = Bullet(0, 100, 0, FakeImage(), speed=600)
            game_world.add_object(enemy, depth=1)
            game_world.add_object(bullet, depth=2)

            bullet.update()

        self.assertIs(bullet.hit_target, enemy)
        self.assertIs(bullet.hit_result, HitResult.HIT)
        self.assertNotIn(bullet, game_world.world[2])
        self.assertEqual(enemy.hp, enemy.max_hp - bullet.damage)

    def test_bullet_does_not_hit_enemy_outside_collision_radius(self):
        enemy = Enemy(100, 100, ENEMY_STATS[EnemyType.BASIC])
        bullet = Bullet(0, 100, 0, FakeImage(), speed=600)
        game_world.add_object(enemy, depth=1)
        game_world.add_object(bullet, depth=2)

        bullet.update()

        self.assertIsNone(bullet.hit_target)
        self.assertIn(bullet, game_world.world[2])

    def test_hit_results_apply_their_configured_enemy_damage(self):
        cases = (
            (HitResult.MISS, 0, 20),
            (HitResult.HIT, 5, 15),
            (HitResult.HEADSHOT, 15, 5),
        )
        for result, damage, expected_hp in cases:
            with self.subTest(result=result), patch(
                "bullet.roll_hit_result",
                return_value=result,
            ):
                enemy = Enemy(20, 100, ENEMY_STATS[EnemyType.BASIC])
                bullet = Bullet(0, 100, 0, FakeImage(), speed=600, damage=5)
                game_world.add_object(enemy, depth=1)
                game_world.add_object(bullet, depth=2)

                bullet.update()

                self.assertIs(bullet.hit_result, result)
                self.assertEqual(bullet.damage_dealt, damage)
                self.assertEqual(enemy.hp, expected_hp)
                game_world.clear()


if __name__ == "__main__":
    unittest.main()
