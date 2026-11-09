import unittest

from enemy import Enemy, EnemyStats


class FakeImage:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class EnemyTests(unittest.TestCase):
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
