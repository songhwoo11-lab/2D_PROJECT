import unittest

from enemy import ENEMY_STATS, EnemyType
from enemy_types import BasicEnemy
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


if __name__ == "__main__":
    unittest.main()
