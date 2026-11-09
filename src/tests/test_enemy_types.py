import unittest

from enemy import ENEMY_STATS, EnemyType
from enemy_types import BasicEnemy, TankerEnemy
from player import Player


class BasicEnemyTests(unittest.TestCase):
    def test_basic_enemy_uses_prd_stats_and_shared_behavior(self):
        enemy = BasicEnemy(0, 0, player=Player(100, 0))

        self.assertEqual(enemy.stats, ENEMY_STATS[EnemyType.BASIC])
        self.assertEqual((enemy.max_hp, enemy.attack_damage), (20, 8))
        self.assertEqual(enemy.attack_interval, 0.8)
        enemy.update()
        self.assertGreater(enemy.x, 0)
        self.assertTrue(enemy.is_alive)


class TankerEnemyTests(unittest.TestCase):
    def test_tanker_enemy_uses_high_health_stats_and_common_behavior(self):
        enemy = TankerEnemy(0, 0)

        self.assertEqual(enemy.stats, ENEMY_STATS[EnemyType.TANKER])
        self.assertEqual((enemy.max_hp, enemy.attack_damage), (120, 5))
        self.assertEqual(enemy.attack_interval, 2.0)
        self.assertFalse(enemy.take_damage(100))
        self.assertEqual(enemy.hp, 20)
        self.assertTrue(enemy.take_damage(20))


if __name__ == "__main__":
    unittest.main()
