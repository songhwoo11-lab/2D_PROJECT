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


if __name__ == "__main__":
    unittest.main()
