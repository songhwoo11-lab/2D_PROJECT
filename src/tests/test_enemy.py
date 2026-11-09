import unittest

from enemy import ENEMY_STATS, Enemy, EnemyStats, EnemyType


class FakeImage:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class EnemyTests(unittest.TestCase):
    def test_enemy_type_stats_match_prd(self):
        expected = {
            EnemyType.BASIC: (20, 8, 0.8, 0),
            EnemyType.EXPLOSIVE: (80, 15, 1.5, 20),
            EnemyType.TANKER: (120, 5, 2.0, 0),
            EnemyType.ASSASSIN: (10, 10, 0.5, 0),
            EnemyType.ARCHER: (50, 10, 1.2, 150),
        }

        for enemy_type, (hp, damage, interval, attack_range) in expected.items():
            with self.subTest(enemy_type=enemy_type):
                stats = ENEMY_STATS[enemy_type]
                self.assertEqual(stats.max_hp, hp)
                self.assertEqual(stats.attack_damage, damage)
                self.assertEqual(stats.attack_interval, interval)
                self.assertEqual(stats.attack_range, attack_range)

    def test_enemy_initializes_shared_combat_state(self):
        stats = EnemyStats("test", 20, 8, 0.8, 60, radius=12)
        enemy = Enemy(10, 20, stats)

        self.assertEqual((enemy.x, enemy.y), (10.0, 20.0))
        self.assertEqual((enemy.hp, enemy.max_hp), (20.0, 20.0))
        self.assertEqual(enemy.attack_damage, 8)
        self.assertEqual(enemy.attack_interval, 0.8)
        self.assertTrue(enemy.is_alive)

    def test_damage_clamps_health_and_marks_enemy_dead(self):
        enemy = Enemy(0, 0, EnemyStats("test", 20, 8, 1, 0))

        self.assertFalse(enemy.take_damage(5))
        self.assertEqual(enemy.hp, 15)
        self.assertTrue(enemy.take_damage(20))
        self.assertEqual(enemy.hp, 0)
        self.assertFalse(enemy.is_alive)

    def test_negative_damage_and_invalid_stats_are_rejected(self):
        enemy = Enemy(0, 0, EnemyStats("test", 20, 8, 1, 0))
        with self.assertRaisesRegex(ValueError, "non-negative"):
            enemy.take_damage(-1)
        with self.assertRaisesRegex(ValueError, "max_hp"):
            Enemy(0, 0, EnemyStats("bad", 0, 0, 1, 0))

    def test_draw_uses_injected_image_and_screen_position(self):
        image = FakeImage()
        enemy = Enemy(10, 20, EnemyStats("test", 20, 8, 1, 0, radius=12), image=image)
        enemy.set_screen_position(100, 200)

        enemy.draw()

        self.assertEqual(image.calls, [(100, 200, 24, 24)])


if __name__ == "__main__":
    unittest.main()
