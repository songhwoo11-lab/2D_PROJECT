import math
import unittest
from unittest.mock import patch

import pico2d
from arrow import Arrow
from enemy import ENEMY_STATS, EnemyType
from enemy_types import (
    ArcherEnemy,
    AssassinEnemy,
    BasicEnemy,
    ExplosiveEnemy,
    TankerEnemy,
)
from explosion import Explosion, ExplosionTarget
import game_world
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
        self.assertEqual(enemy.move_speed, 120)
        self.assertTrue(enemy.take_damage(10))

    def test_assassin_moves_at_twice_the_default_enemy_speed(self):
        enemy = AssassinEnemy(0, 0, player=Player(1000, 0))

        enemy.update()

        self.assertEqual(enemy.x, 2)
        self.assertEqual(enemy.y, 0)

    def test_assassin_opacity_fades_linearly_with_player_distance(self):
        player = Player(0, 0)
        enemy = AssassinEnemy(125, 0, player=player)

        self.assertEqual(enemy.opacity_alpha, round((1 - 125 / 150) * 255))
        enemy.x = 150
        self.assertEqual(enemy.opacity_alpha, 0)
        enemy.x = 0
        self.assertEqual(enemy.opacity_alpha, 255)

    def test_assassin_hit_temporarily_overrides_distance_fade(self):
        enemy = AssassinEnemy(200, 0, player=Player(0, 0))
        self.assertEqual(enemy.opacity_alpha, 0)

        enemy.take_damage(1)

        self.assertEqual(enemy.opacity_alpha, 255)
        for _ in range(round(enemy.HIT_FLASH_DURATION_SECONDS * 60) - 1):
            enemy.update()
            self.assertEqual(enemy.opacity_alpha, 255)

        enemy.update()

        self.assertEqual(enemy.opacity_alpha, 0)

    def test_zero_damage_does_not_trigger_assassin_hit_flash(self):
        enemy = AssassinEnemy(200, 0, player=Player(0, 0))

        enemy.take_damage(0)

        self.assertEqual(enemy.opacity_alpha, 0)

    def test_assassin_is_not_drawn_outside_fade_distance(self):
        image = type("Image", (), {"texture": object(), "draw": lambda *args: None})()
        rectangles = []
        enemy = AssassinEnemy(
            151,
            0,
            image=image,
            player=Player(0, 0),
            draw_rectangle=lambda *args: rectangles.append(args),
        )

        with patch.object(pico2d, "SDL_SetTextureBlendMode") as set_blend_mode, patch.object(
            pico2d,
            "SDL_SetTextureAlphaMod",
        ) as set_alpha:
            enemy.draw()

        set_blend_mode.assert_not_called()
        set_alpha.assert_not_called()
        self.assertEqual(rectangles, [])

    def test_assassin_sprite_fades_before_health_bar_is_revealed(self):
        class FakeImage:
            texture = object()

            def __init__(self):
                self.draw_calls = []

            def draw(self, *args):
                self.draw_calls.append(args)

        image = FakeImage()
        rectangles = []
        enemy = AssassinEnemy(
            110,
            0,
            image=image,
            player=Player(0, 0),
            draw_rectangle=lambda *args: rectangles.append(args),
        )

        with patch.object(pico2d, "SDL_SetTextureBlendMode", return_value=0), patch.object(
            pico2d,
            "SDL_SetTextureAlphaMod",
            return_value=0,
        ) as set_alpha:
            enemy.draw()

        self.assertEqual(len(image.draw_calls), 1)
        self.assertEqual(
            set_alpha.call_args_list[0].args[1],
            round((1 - 110 / 150) * 255),
        )
        self.assertEqual(set_alpha.call_args_list[-1].args[1], 255)
        self.assertEqual(rectangles, [])

    def test_assassin_health_bar_appears_within_100_units(self):
        image = type("Image", (), {"texture": object(), "draw": lambda *args: None})()
        rectangles = []
        enemy = AssassinEnemy(
            100,
            0,
            image=image,
            player=Player(0, 0),
            draw_rectangle=lambda *args: rectangles.append(args),
        )

        with patch.object(pico2d, "SDL_SetTextureBlendMode", return_value=0), patch.object(
            pico2d,
            "SDL_SetTextureAlphaMod",
            return_value=0,
        ):
            enemy.draw()

        self.assertEqual(len(rectangles), 1)
        self.assertEqual(rectangles[0][7], 255)

    def test_hit_while_hidden_temporarily_reveals_health_bar(self):
        image = type("Image", (), {"texture": object(), "draw": lambda *args: None})()
        rectangles = []
        enemy = AssassinEnemy(
            200,
            0,
            image=image,
            player=Player(0, 0),
            draw_rectangle=lambda *args: rectangles.append(args),
        )
        self.assertEqual(enemy.health_bar_alpha, 0)

        enemy.take_damage(1)
        self.assertEqual(enemy.health_bar_alpha, 255)
        with patch.object(pico2d, "SDL_SetTextureBlendMode", return_value=0), patch.object(
            pico2d,
            "SDL_SetTextureAlphaMod",
            return_value=0,
        ):
            enemy.draw()
        self.assertEqual(len(rectangles), 1)
        self.assertEqual(rectangles[0][7], 255)

        for _ in range(round(enemy.HIT_FLASH_DURATION_SECONDS * 60)):
            enemy.update()

        rectangles.clear()
        self.assertEqual(enemy.health_bar_alpha, 0)
        with patch.object(pico2d, "SDL_SetTextureBlendMode", return_value=0), patch.object(
            pico2d,
            "SDL_SetTextureAlphaMod",
        ) as set_alpha:
            enemy.draw()
        set_alpha.assert_not_called()
        self.assertEqual(rectangles, [])


class ArcherEnemyTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_archer_uses_prd_stats_and_charges_inside_range(self):
        player = Player(150, 0)
        enemy = ArcherEnemy(0, 0, player=player)

        self.assertEqual(enemy.stats, ENEMY_STATS[EnemyType.ARCHER])
        self.assertEqual((enemy.max_hp, enemy.attack_damage), (50, 10))
        self.assertEqual(enemy.attack_interval, 1.2)
        enemy.update()

        self.assertGreater(enemy.attack_charge, 0)
        self.assertEqual((enemy.x, enemy.y), (0, 0))

    def test_archer_charge_reaches_warning_in_half_original_time(self):
        enemy = ArcherEnemy(0, 0, player=Player(150, 0))
        charge_duration_frames = round(
            enemy.attack_interval * 60 / enemy.CHARGE_SPEED_MULTIPLIER
        )

        for _ in range(charge_duration_frames - 1):
            enemy.update()
        self.assertFalse(enemy.is_attack_warning)
        self.assertLess(enemy.attack_charge, 1)

        enemy.update()

        self.assertTrue(enemy.is_attack_warning)
        self.assertEqual(enemy.attack_charge, 1)

    def test_archer_warns_then_attacks_after_charge(self):
        player = Player(150, 0)
        enemy = ArcherEnemy(0, 0, player=player)

        charge_duration_frames = round(
            enemy.attack_interval * 60 / enemy.CHARGE_SPEED_MULTIPLIER
        )
        for _ in range(charge_duration_frames):
            enemy.update()
        self.assertTrue(enemy.is_attack_warning)
        self.assertEqual(player.hp, 100)

        for _ in range(enemy.WARNING_DURATION_FRAMES):
            enemy.update()
        self.assertFalse(enemy.is_attack_warning)
        self.assertEqual(player.hp, 100)
        self.assertEqual(enemy.attack_charge, 0)
        arrow = next(
            obj
            for layer in game_world.world
            for obj in layer
            if isinstance(obj, Arrow)
        )
        while arrow in game_world.world[2]:
            arrow.update()
        self.assertEqual(player.hp, 90)

    def test_archer_shot_spawns_arrow_with_configured_image(self):
        image = type("Image", (), {"rotate_draw": lambda self, *args: None})()
        player = Player(150, 0)
        enemy = ArcherEnemy(0, 0, player=player, arrow_image=image)
        game_world.clear()
        try:
            charge_duration_frames = round(
                enemy.attack_interval * 60 / enemy.CHARGE_SPEED_MULTIPLIER
            )
            for _ in range(charge_duration_frames + enemy.WARNING_DURATION_FRAMES):
                enemy.update()

            arrows = [
                obj
                for layer in game_world.world
                for obj in layer
                if isinstance(obj, Arrow)
            ]
            self.assertEqual(len(arrows), 1)
            self.assertIs(arrows[0].image, image)
            self.assertEqual(player.hp, 100)
            while arrows[0] in game_world.world[2]:
                arrows[0].update()
            self.assertEqual(player.hp, 90)
        finally:
            game_world.clear()

    def test_archer_resets_charge_outside_range_and_moves_toward_range(self):
        player = Player(400, 0)
        enemy = ArcherEnemy(0, 0, player=player)
        enemy.attack_charge = 0.5

        enemy.update()

        self.assertEqual(enemy.attack_charge, 0)
        self.assertGreater(enemy.x, 0)
        self.assertEqual(player.hp, player.max_hp)

    def test_archer_range_is_twice_the_original_value(self):
        archer = ArcherEnemy(0, 0, player=Player(        200, 0))

        self.assertEqual(archer.stats.attack_range, 300)
        archer.update()
        self.assertGreater(archer.attack_charge, 0)
        self.assertEqual((archer.x, archer.y), (0, 0))

        archer.player.x = 300.01
        archer.update()
        self.assertEqual(archer.attack_charge, 0)
        self.assertGreater(archer.x, 0)

    def test_archer_starts_charging_at_floating_point_range_boundary(self):
        angle = 0.0022
        player = Player(
            math.cos(angle) * 300.5,
            math.sin(angle) * 300.5,
        )
        archer = ArcherEnemy(0, 0, player=player)

        archer.update()
        self.assertEqual(archer.attack_charge, 0)
        archer.update()

        self.assertGreater(archer.attack_charge, 0)

    def test_archer_does_not_move_through_another_enemy(self):
        player = Player(1000, 0)
        archer = ArcherEnemy(0, 0, player=player)
        obstacle = BasicEnemy(50, 0, player=player)
        game_world.add_object(archer, depth=1)
        game_world.add_object(obstacle, depth=1)

        for _ in range(40):
            archer.update()

        self.assertGreaterEqual(
            math.hypot(archer.x - obstacle.x, archer.y - obstacle.y) + 1e-6,
            archer.radius + obstacle.radius,
        )

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

    def test_archer_warning_charge_bar_is_yellow(self):
        rectangles = []
        enemy = ArcherEnemy(
            100,
            100,
            image=type("Image", (), {"draw": lambda self, *args: None})(),
            draw_rectangle=lambda *args: rectangles.append(args),
        )
        enemy.attack_charge = 1.0
        enemy.attack_warning_remaining = 1

        enemy.draw()

        self.assertEqual(rectangles[1][4:7], (255, 220, 40))


class ExplosiveEnemyTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_explosive_enemy_uses_prd_stats_and_player_only_attack(self):
        player = Player(20, 0)
        nearby_enemy = BasicEnemy(0, 0)
        explosive = ExplosiveEnemy(0, 0, player=player)
        game_world.add_object(nearby_enemy, depth=1)

        explosive.update()

        self.assertEqual(player.hp, 85)
        self.assertEqual(nearby_enemy.hp, nearby_enemy.max_hp)
        self.assertEqual((explosive.max_hp, explosive.attack_damage), (80, 15))
        self.assertEqual(explosive.attack_interval, 1.5)
        self.assertFalse(explosive.is_alive)

    def test_explosive_enemy_attacks_at_floating_point_range_boundary(self):
        angle = 0.0023
        player = Player(
            math.cos(angle) * 50.5,
            math.sin(angle) * 50.5,
        )
        explosive = ExplosiveEnemy(0, 0, player=player)

        explosive.update()
        self.assertEqual(player.hp, player.max_hp)
        explosive.update()

        self.assertEqual(player.hp, player.max_hp - explosive.EXPLOSION_DAMAGE)

    def test_explosive_enemy_does_not_move_through_another_enemy(self):
        player = Player(1000, 0)
        explosive = ExplosiveEnemy(0, 0, player=player)
        obstacle = BasicEnemy(50, 0, player=player)
        game_world.add_object(explosive, depth=1)
        game_world.add_object(obstacle, depth=1)

        for _ in range(40):
            explosive.update()

        self.assertGreaterEqual(
            math.hypot(
                explosive.x - obstacle.x,
                explosive.y - obstacle.y,
            )
            + 1e-6,
            explosive.radius + obstacle.radius,
        )

    def test_explosive_enemy_player_attack_has_50_unit_range(self):
        player = Player(50, 0)
        nearby_enemy = BasicEnemy(0, 0)
        explosive = ExplosiveEnemy(0, 0, player=player)
        game_world.add_object(nearby_enemy, depth=1)

        explosive.update()

        self.assertEqual(player.hp, player.max_hp - explosive.EXPLOSION_DAMAGE)
        self.assertFalse(explosive.is_alive)
        self.assertEqual(nearby_enemy.hp, nearby_enemy.max_hp)

    def test_explosive_death_blast_has_50_unit_range(self):
        player = Player(0, 0)
        inside = BasicEnemy(49, 0)
        outside = BasicEnemy(50.01, 0)
        explosive = ExplosiveEnemy(0, 0, player=player)
        game_world.add_object(inside, depth=1)
        game_world.add_object(outside, depth=1)
        game_world.add_object(explosive, depth=1)

        explosive.take_damage(explosive.max_hp)

        self.assertEqual(inside.hp, inside.max_hp - explosive.EXPLOSION_DAMAGE)
        self.assertEqual(outside.hp, outside.max_hp)
        self.assertEqual(player.hp, player.max_hp)

    def test_explosive_enemy_death_only_damages_nearby_enemies(self):
        player = Player(0, 0)
        victim = BasicEnemy(15, 0)
        distant = BasicEnemy(100, 0)
        explosive = ExplosiveEnemy(0, 0, player=player)
        game_world.add_object(victim, depth=1)
        game_world.add_object(distant, depth=1)
        game_world.add_object(explosive, depth=1)

        self.assertTrue(explosive.take_damage(explosive.max_hp))
        self.assertEqual(victim.hp, victim.max_hp - 15)
        self.assertEqual(distant.hp, distant.max_hp)
        self.assertEqual(player.hp, player.max_hp)

    def test_explosion_hits_only_selected_targets_once_with_fixed_radius(self):
        player = Player(20, 0)
        enemy = BasicEnemy(20, 0)
        player_explosion = Explosion(
            0,
            0,
            20,
            15,
            ExplosionTarget.PLAYER_ONLY,
        )
        self.assertEqual(player_explosion.apply(player, [enemy]), (player,))
        self.assertEqual(player_explosion.apply(player, [enemy]), ())
        self.assertEqual((player.hp, enemy.hp), (85, enemy.max_hp))

        enemy_explosion = Explosion(
            0,
            0,
            20,
            15,
            ExplosionTarget.ENEMIES_ONLY,
        )
        self.assertEqual(enemy_explosion.apply(player, [enemy]), (enemy,))
        self.assertEqual((player.hp, enemy.hp), (85, enemy.max_hp - 15))


if __name__ == "__main__":
    unittest.main()
