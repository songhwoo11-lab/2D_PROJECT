import unittest

from enemy import ENEMY_STATS, EnemyType
from enemy_types import ArcherEnemy, AssassinEnemy, BasicEnemy, TankerEnemy
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


class AssassinEnemyTests(unittest.TestCase):
    def test_assassin_enemy_uses_low_health_high_damage_stats(self):
        enemy = AssassinEnemy(0, 0)

        self.assertEqual(enemy.stats, ENEMY_STATS[EnemyType.ASSASSIN])
        self.assertEqual((enemy.max_hp, enemy.attack_damage), (10, 10))
        self.assertEqual(enemy.attack_interval, 0.5)
        self.assertTrue(enemy.take_damage(10))


class ArcherEnemyTests(unittest.TestCase):
    def test_archer_uses_prd_stats_and_charges_inside_range(self):
        player = Player(150, 0)
        enemy = ArcherEnemy(0, 0, player=player)

        self.assertEqual(enemy.stats, ENEMY_STATS[EnemyType.ARCHER])
        self.assertEqual((enemy.max_hp, enemy.attack_damage), (50, 10))
        self.assertEqual(enemy.attack_interval, 1.2)
        enemy.update()

        self.assertGreater(enemy.attack_charge, 0)
        self.assertEqual((enemy.x, enemy.y), (0, 0))

    def test_archer_warns_then_attacks_after_charge(self):
        player = Player(150, 0)
        enemy = ArcherEnemy(0, 0, player=player)

        for _ in range(round(enemy.attack_interval * 60)):
            enemy.update()
        self.assertTrue(enemy.is_attack_warning)
        self.assertEqual(player.hp, 100)

        for _ in range(enemy.WARNING_DURATION_FRAMES):
            enemy.update()
        self.assertFalse(enemy.is_attack_warning)
        self.assertEqual(player.hp, 90)
        self.assertEqual(enemy.attack_charge, 0)

    def test_archer_resets_charge_outside_range_and_moves_toward_range(self):
        player = Player(250, 0)
        enemy = ArcherEnemy(0, 0, player=player)
        enemy.attack_charge = 0.5

        enemy.update()

        self.assertEqual(enemy.attack_charge, 0)
        self.assertGreater(enemy.x, 0)
        self.assertEqual(player.hp, player.max_hp)

    def test_archer_draws_attack_charge_bar_above_health_bar(self):
        rectangles = []

        def draw_rectangle(*args):
            rectangles.append(args)

        enemy = ArcherEnemy(
            100,
            100,
            image=type("Image", (), {"draw": lambda self, *args: None})(),
            draw_rectangle=draw_rectangle,
        )
        enemy.attack_charge = 0.5

        enemy.draw()

        self.assertEqual(len(rectangles), 2)
        self.assertLess(rectangles[0][1], rectangles[1][1])


if __name__ == "__main__":
    unittest.main()
