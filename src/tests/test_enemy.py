import unittest

from enemy import ENEMY_STATS, Enemy, EnemyStats, EnemyType
from player import Player


class FakeImage:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class FakeRectangle:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
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
        draw_rectangle = FakeRectangle()
        enemy = Enemy(
            10,
            20,
            EnemyStats("test", 20, 8, 1, 0, radius=12),
            image=image,
            draw_rectangle=draw_rectangle,
        )
        enemy.set_screen_position(100, 200)

        enemy.draw()

        self.assertEqual(image.calls, [(100, 200, 24, 24)])
        self.assertEqual(draw_rectangle.calls, [(88, 215, 112, 219, 255, 0, 0, 255, True)])

    def test_health_bar_width_tracks_health_without_text(self):
        draw_rectangle = FakeRectangle()
        enemy = Enemy(
            10,
            20,
            EnemyStats("test", 20, 8, 1, 0, radius=10),
            image=FakeImage(),
            draw_rectangle=draw_rectangle,
        )
        enemy.take_damage(5)

        enemy.draw()

        self.assertEqual(draw_rectangle.calls, [(0, 33, 15, 37, 255, 0, 0, 255, True)])

    def test_draw_requires_explicit_rendering_dependencies(self):
        with self.assertRaisesRegex(RuntimeError, "loaded enemy image"):
            Enemy(0, 0, EnemyStats("test", 20, 8, 1, 0)).draw()
        with self.assertRaisesRegex(RuntimeError, "rectangle drawing"):
            Enemy(0, 0, EnemyStats("test", 20, 8, 1, 0), image=FakeImage()).draw()

    def test_enemy_tracks_player_at_configured_speed(self):
        player = Player(100, 0)
        enemy = Enemy(
            0,
            0,
            EnemyStats("test", 20, 8, 1, 60, radius=10),
            player=player,
        )

        enemy.update()

        self.assertAlmostEqual(enemy.x, 1)
        self.assertEqual(enemy.y, 0)
        self.assertEqual(enemy.velocity_x, 1)
        self.assertEqual(enemy.velocity_y, 0)

    def test_player_collision_uses_combined_circular_radii(self):
        player = Player(0, 0, radius=10)
        enemy = Enemy(
            0,
            0,
            EnemyStats("test", 20, 8, 1, 0, radius=5),
            player=player,
        )

        enemy.x = 15
        self.assertTrue(enemy.collides_with(player))
        enemy.x = 15.01
        self.assertFalse(enemy.collides_with(player))

    def test_contact_attack_applies_damage_on_interval(self):
        player = Player(0, 0, radius=10)
        enemy = Enemy(
            20,
            0,
            EnemyStats("test", 20, 8, 0.8, 60, radius=10),
            player=player,
        )

        enemy.update()
        self.assertEqual(player.hp, 92)

        for _ in range(47):
            enemy.update()
        self.assertEqual(player.hp, 92)

        enemy.update()
        self.assertEqual(player.hp, 84)

    def test_attacker_does_not_damage_outside_contact(self):
        player = Player(100, 0)
        enemy = Enemy(
            0,
            0,
            EnemyStats("test", 20, 8, 1, 0),
            player=player,
        )

        enemy.update()

        self.assertEqual(player.hp, player.max_hp)

    def test_enemy_stops_attacking_after_player_is_defeated(self):
        player = Player(0, 0, max_hp=5, radius=10)
        enemy = Enemy(
            20,
            0,
            EnemyStats("test", 20, 8, 0.1, 60, radius=10),
            player=player,
        )

        enemy.update()
        self.assertEqual(player.hp, 0)
        for _ in range(10):
            enemy.update()
        self.assertEqual(player.hp, 0)

    def test_enemy_stops_at_contact_distance_and_without_target(self):
        player = Player(25, 0, radius=10)
        enemy = Enemy(
            0,
            0,
            EnemyStats("test", 20, 8, 1, 2000, radius=10),
            player=player,
        )

        enemy.update()

        self.assertEqual(enemy.x, 5)
        self.assertEqual(enemy.y, 0)
        self.assertEqual((enemy.velocity_x, enemy.velocity_y), (1, 0))

        targetless = Enemy(0, 0, EnemyStats("test", 20, 8, 1, 60))
        targetless.update()
        self.assertEqual((targetless.x, targetless.y), (0, 0))


if __name__ == "__main__":
    unittest.main()
