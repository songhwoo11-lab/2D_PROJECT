import unittest

from enemy import ENEMY_STATS, Enemy, EnemyType


class EnemyStatScalingTests(unittest.TestCase):
    def _enemy(self):
        return Enemy(0.0, 0.0, ENEMY_STATS[EnemyType.BASIC])

    def test_multiplier_scales_health_and_attack(self):
        enemy = self._enemy()
        base_hp = enemy.max_hp
        base_attack = enemy.attack_damage

        enemy.apply_stat_multiplier(2.0)

        self.assertEqual(enemy.max_hp, base_hp * 2.0)
        self.assertEqual(enemy.hp, enemy.max_hp)
        self.assertEqual(enemy.attack_damage, base_attack * 2.0)

    def test_scaling_refills_health_to_the_new_maximum(self):
        enemy = self._enemy()
        enemy.take_damage(5)

        enemy.apply_stat_multiplier(4.0)

        self.assertEqual(enemy.hp, enemy.max_hp)

    def test_negative_multiplier_is_rejected(self):
        enemy = self._enemy()

        with self.assertRaises(ValueError):
            enemy.apply_stat_multiplier(-1)


class EnemyHpTrailTests(unittest.TestCase):
    def _enemy(self):
        return Enemy(0.0, 0.0, ENEMY_STATS[EnemyType.BASIC])

    def test_damage_keeps_the_trailing_hp_during_the_delay(self):
        enemy = self._enemy()

        enemy.take_damage(10)
        enemy.update_hp_trail(0.1)

        self.assertEqual(enemy.hp, 10)
        self.assertEqual(enemy.hp_trail.value, 20)

    def test_trailing_hp_drains_after_the_delay(self):
        enemy = self._enemy()
        enemy.take_damage(10)
        enemy.update_hp_trail(enemy.hp_trail.delay)

        enemy.update_hp_trail(0.05)

        self.assertLess(enemy.hp_trail.value, 20)
        self.assertGreater(enemy.hp_trail.value, 10)

    def test_stat_multiplier_resets_the_trailing_hp(self):
        enemy = self._enemy()
        enemy.take_damage(10)

        enemy.apply_stat_multiplier(2.0)

        self.assertEqual(enemy.hp_trail.value, enemy.max_hp)
        self.assertEqual(enemy.hp_trail.max_hp, enemy.max_hp)

    def test_health_bar_draws_the_trailing_hp_behind_the_current_hp(self):
        enemy = self._enemy()
        rectangles = []
        enemy.draw_rectangle = lambda *args: rectangles.append(args)
        enemy.take_damage(10)
        enemy.update_hp_trail(0.0)

        enemy.draw_health_bar(0.0, 0.0)

        trailing, current = rectangles
        bar_left = -enemy.radius
        bar_width = enemy.radius * 2
        self.assertAlmostEqual(trailing[2], bar_left + bar_width)
        self.assertAlmostEqual(current[2], bar_left + bar_width * 0.5)


if __name__ == "__main__":
    unittest.main()
