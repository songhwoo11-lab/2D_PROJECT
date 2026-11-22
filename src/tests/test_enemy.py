import unittest
from unittest.mock import patch

import game_world
from enemy import (
    DAMAGE_SOURCE_EXPLOSION,
    ENEMY_STATS,
    Enemy,
    EnemyType,
)
from enemy_types import AssassinEnemy, BasicEnemy


class FakePlayer:
    def __init__(self):
        self.x = 200.0
        self.y = 0.0
        self.radius = 20.0
        self.is_defeated = False
        self.damage_taken = []

    def take_damage(self, amount):
        self.damage_taken.append(amount)


class FakeAssassinImage:
    texture = "assassin-texture"

    def draw(self, x, y, w=None, h=None):
        pass


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


class EnemyDamageSourceTests(unittest.TestCase):
    def _enemy(self):
        return Enemy(0.0, 0.0, ENEMY_STATS[EnemyType.BASIC])

    def test_default_damage_source_is_none(self):
        self.assertIsNone(self._enemy().last_damage_source)

    def test_damage_source_is_recorded(self):
        enemy = self._enemy()

        enemy.take_damage(5, source=DAMAGE_SOURCE_EXPLOSION)

        self.assertEqual(enemy.last_damage_source, DAMAGE_SOURCE_EXPLOSION)

    def test_zero_damage_keeps_the_previous_source(self):
        enemy = self._enemy()
        enemy.take_damage(5, source=DAMAGE_SOURCE_EXPLOSION)

        enemy.take_damage(0)

        self.assertEqual(enemy.last_damage_source, DAMAGE_SOURCE_EXPLOSION)

    def test_damage_after_death_keeps_the_lethal_source(self):
        enemy = self._enemy()
        enemy.take_damage(enemy.hp, source=DAMAGE_SOURCE_EXPLOSION)

        enemy.take_damage(5)

        self.assertEqual(enemy.last_damage_source, DAMAGE_SOURCE_EXPLOSION)


class AssassinStealthTests(unittest.TestCase):
    def setUp(self):
        self.player = FakePlayer()
        self.assassin = AssassinEnemy(0, 0, player=self.player)

    def test_reveal_range_is_extended_by_fifty(self):
        self.assertEqual(AssassinEnemy.FADE_DISTANCE, 350.0)

    def test_assassin_is_visible_at_the_previous_reveal_edge(self):
        self.assassin.x = self.player.x - 300.0

        self.assertGreater(self.assassin.opacity_alpha, 0)

    def test_assassin_is_hidden_at_the_new_reveal_edge(self):
        self.assassin.x = self.player.x - AssassinEnemy.FADE_DISTANCE

        self.assertEqual(self.assassin.opacity_alpha, 0)

    def test_assassin_is_fully_visible_up_close(self):
        self.assassin.x = self.player.x

        self.assertEqual(self.assassin.opacity_alpha, 255)

    def test_opacity_is_maximal_when_health_bar_is_visible(self):
        self.assassin.x = self.player.x - AssassinEnemy.HEALTH_BAR_DISTANCE

        self.assertEqual(self.assassin.health_bar_alpha, 255)
        self.assertEqual(self.assassin.opacity_alpha, 255)

    def test_opacity_fades_when_health_bar_is_hidden(self):
        self.assassin.x = self.player.x - AssassinEnemy.HEALTH_BAR_DISTANCE - 1.0

        self.assertEqual(self.assassin.health_bar_alpha, 0)
        self.assertLess(self.assassin.opacity_alpha, 255)


class AssassinAttackTests(unittest.TestCase):
    def setUp(self):
        self.player = FakePlayer()
        self.assassin = AssassinEnemy(0, 0, player=self.player)

    def test_attack_starts_only_when_fully_visible(self):
        self.player.x = 400.0
        self.assassin.update(0.1)
        self.assertFalse(self.assassin.is_preparing_attack)

        self.player.x = 150.0
        self.assassin.update(0.1)
        self.assertTrue(self.assassin.is_preparing_attack)

    def test_attack_can_start_when_hit_flash_reveals_the_health_bar(self):
        self.player.x = 300.0
        self.assassin.take_damage(1)

        self.assassin.update(0.05)

        self.assertTrue(self.assassin.health_bar_alpha > 0)
        self.assertTrue(self.assassin.is_preparing_attack)

    def test_assassin_does_not_move_during_preparation(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        position = (self.assassin.x, self.assassin.y)

        self.assassin.update(0.5)
        self.assassin.update(0.3)

        self.assertEqual((self.assassin.x, self.assassin.y), position)
        self.assertTrue(self.assassin.is_preparing_attack)

        self.assassin.update(0.2)
        self.assertFalse(self.assassin.is_preparing_attack)
        self.assertAlmostEqual(self.assassin.x, 400.0)
        self.assertAlmostEqual(self.assassin.y, 0.0)

    def test_assassin_stays_visible_during_preparation_outside_reveal_range(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        self.player.x = 1000.0

        self.assertTrue(self.assassin.is_preparing_attack)
        self.assertEqual(self.assassin.opacity_alpha, 255)
        self.assertEqual(self.assassin.health_bar_alpha, 255)

    def test_assassin_stays_visible_during_the_strike_outside_reveal_range(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        self.assassin.update(1.0)

        self.assertTrue(self.assassin.is_strike_visible)
        self.assertEqual(self.assassin.opacity_alpha, 255)
        self.assertEqual(self.assassin.health_bar_alpha, 255)

    def test_direction_tracks_player_only_for_the_first_half_second(self):
        self.player.x = 150.0
        self.assassin.update(0.25)
        self.assertEqual(self.assassin.attack_direction, (1.0, 0.0))

        self.player.x = 0.0
        self.player.y = 150.0
        self.assassin.update(0.25)
        self.assertEqual(self.assassin.attack_direction, (0.0, 1.0))

        self.player.x = -150.0
        self.player.y = 0.0
        self.assassin.update(0.1)
        self.assertEqual(self.assassin.attack_direction, (0.0, 1.0))

    def test_strike_hits_player_on_the_line_after_one_second(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        self.assassin.update(1.0)

        self.assertEqual(self.player.damage_taken, [self.assassin.attack_damage])
        self.assertIsNone(self.assassin.last_damage_source)
        self.assertFalse(self.assassin.is_preparing_attack)
        self.assertTrue(self.assassin.is_strike_visible)
        self.assertAlmostEqual(self.assassin.x, 400.0)
        self.assertAlmostEqual(self.assassin.y, 0.0)

    def test_strike_does_not_hit_player_beyond_four_hundred(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        self.assassin.update(0.6)
        self.player.x = 600.0
        self.assassin.update(0.4)

        self.assertEqual(self.player.damage_taken, [])
        self.assertAlmostEqual(self.assassin.x, 400.0)
        self.assertAlmostEqual(self.assassin.y, 0.0)

    def test_dash_uses_the_locked_direction_even_after_the_player_moves(self):
        self.player.x = 0.0
        self.player.y = 150.0
        self.assassin.update(0.1)
        self.assassin.update(0.4)
        self.assassin.update(0.1)
        self.player.x = -300.0
        self.player.y = 0.0
        self.assassin.update(0.4)

        self.assertEqual(self.player.damage_taken, [])
        self.assertAlmostEqual(self.assassin.x, 0.0)
        self.assertAlmostEqual(self.assassin.y, 400.0)

    def test_melee_attack_is_restored_at_contact(self):
        self.player.x = self.assassin.radius + self.player.radius

        self.assassin.update(0.05)

        self.assertEqual(self.player.damage_taken, [self.assassin.attack_damage])
        self.assertFalse(self.assassin.is_preparing_attack)
        self.assertAlmostEqual(
            self.assassin._attack_cooldown_remaining,
            self.assassin.attack_interval,
        )

    def test_melee_does_not_trigger_just_outside_old_contact_range(self):
        contact_distance = self.assassin.radius + self.player.radius
        self.player.x = contact_distance + 1.0

        self.assassin.update(0.05)

        self.assertEqual(self.player.damage_taken, [])
        self.assertTrue(self.assassin.is_preparing_attack)

    def test_attack_cooldown_delays_the_next_preparation(self):
        self.player.x = 150.0
        self.assassin.update(0.1)
        self.assassin.update(1.0)
        self.assertEqual(len(self.player.damage_taken), 1)

        self.assassin.update(0.1)
        self.assertFalse(self.assassin.is_preparing_attack)

        self.assassin.update(0.5)
        self.assassin.update(0.1)
        self.assertTrue(self.assassin.is_preparing_attack)

    def test_strike_line_is_drawn_with_the_same_range(self):
        self.assassin.draw_rectangle = lambda *args: None
        self.assassin.image = FakeAssassinImage()
        self.assassin._screen_position = (100.0, 200.0)
        self.player.x = 150.0
        self.assassin.update(0.1)

        with patch("enemy_types.pico2d.SDL_SetTextureBlendMode", return_value=0), patch(
            "enemy_types.pico2d.SDL_SetTextureAlphaMod", return_value=0
        ), patch("enemy_types.pico2d.draw_line") as draw_line:
            self.assassin.draw()
        draw_line.assert_called_once_with(
            100.0, 200.0, 500.0, 200.0, 255, 200, 60, 255
        )

        self.assassin.update(1.0)
        self.assassin.set_screen_position(500.0, 200.0)
        with patch("enemy_types.pico2d.SDL_SetTextureBlendMode", return_value=0), patch(
            "enemy_types.pico2d.SDL_SetTextureAlphaMod", return_value=0
        ), patch("enemy_types.pico2d.draw_line") as draw_line:
            self.assassin.draw()
        draw_line.assert_called_once_with(
            100.0, 200.0, 500.0, 200.0, 255, 245, 150, 255
        )


class EnemyCollisionTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def move_past(self, mover, blocker):
        game_world.add_object(mover)
        game_world.add_object(blocker)
        moved = mover.move_towards(200.0, 0.0, 100.0)
        return moved, (mover.x, mover.y)

    def assert_passed_through(self, mover, blocker):
        moved, position = self.move_past(mover, blocker)

        self.assertTrue(moved)
        self.assertAlmostEqual(position[0], 100.0)
        self.assertAlmostEqual(position[1], 0.0)

    def test_assassin_ignores_other_enemies_when_moving(self):
        self.assert_passed_through(
            AssassinEnemy(0, 0, player=FakePlayer()),
            BasicEnemy(50, 0, player=FakePlayer()),
        )

    def test_other_enemies_ignore_assassins_when_moving(self):
        self.assert_passed_through(
            BasicEnemy(0, 0, player=FakePlayer()),
            AssassinEnemy(50, 0, player=FakePlayer()),
        )

    def test_assassins_ignore_each_other_when_moving(self):
        self.assert_passed_through(
            AssassinEnemy(0, 0, player=FakePlayer()),
            AssassinEnemy(50, 0, player=FakePlayer()),
        )

    def test_non_assassins_still_avoid_each_other(self):
        mover = BasicEnemy(0, 0, player=FakePlayer())
        game_world.add_object(mover)
        game_world.add_object(BasicEnemy(50, 0, player=FakePlayer()))

        mover.move_towards(200.0, 0.0, 100.0)

        self.assertLess(mover.x, 0.0)

    def test_assassins_are_excluded_from_the_spatial_index(self):
        assassin = AssassinEnemy(0, 0, player=FakePlayer())
        observer = BasicEnemy(0, 0, player=FakePlayer())
        other = BasicEnemy(10, 0, player=FakePlayer())
        for enemy in (assassin, observer, other):
            game_world.add_object(enemy)

        game_world._build_spatial_index()
        candidates = game_world.nearby_spatial_objects(observer, 200.0)

        self.assertNotIn(assassin, candidates)
        self.assertIn(other, candidates)

    def test_assassin_is_still_hit_by_bullet_collision_checks(self):
        assassin = AssassinEnemy(0, 0, player=FakePlayer())
        basic = BasicEnemy(0, 0, player=FakePlayer())

        self.assertTrue(assassin.collides_with(basic))


if __name__ == "__main__":
    unittest.main()
