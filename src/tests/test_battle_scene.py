import unittest
from unittest.mock import patch

import game_world
from battle_scene import (
    DEBUG_BUTTON_HEIGHT,
    DEBUG_BUTTON_TEXT_Y_OFFSET,
    DEBUG_FONT_SIZE,
    DEBUG_MENU_LEFT,
    BattleScene,
)
from bullet import Bullet
from enemy import EnemyType
from enemy_types import ArcherEnemy, BasicEnemy
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH, WORLD_HEIGHT, WORLD_WIDTH
from player import Player
from weapon import FireMode, Gun


class FakeImage:
    def __init__(self):
        self.draw_calls = []
        self.rotate_calls = []
        self.composite_calls = []

    def draw(self, *args):
        self.draw_calls.append(args)

    def rotate_draw(self, *args):
        self.rotate_calls.append(args)

    def composite_draw(self, *args):
        self.composite_calls.append(args)


class FakeFont:
    def __init__(self):
        self.draw_calls = []

    def draw(self, *args):
        self.draw_calls.append(args)


class FakeBackground:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class BattleSceneTests(unittest.TestCase):
    def setUp(self):
        self.font_measure_patch = patch(
            "hud._measure_text_width",
            side_effect=lambda font, text: len(text) * 10,
        )
        self.font_measure_patch.start()
        self.player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=FakeImage(),
        )
        self.gun = Gun()
        self.background = FakeBackground()
        self.hud_font = FakeFont()
        self.debug_font = FakeFont()
        self.scene = BattleScene(
            self.player,
            self.gun,
            self.background,
            hud_font=self.hud_font,
            debug_font=self.debug_font,
        )
        self.enemy_images = {
            enemy_type: FakeImage() for enemy_type in EnemyType
        }
        self.scene.enemy_images = self.enemy_images
        self.scene.enemy_draw_rectangle = lambda *args: None
        self.debug_circles = []
        self.scene.enemy_draw_circle = lambda *args: self.debug_circles.append(args)
        self.scene.arrow_image = FakeImage()

    def tearDown(self):
        self.scene.close()
        self.font_measure_patch.stop()

    def test_wasd_input_moves_player_and_releases_cleanly(self):
        start_x = self.player.x
        self.scene.key_down("d")
        self.scene.update(1 / 60)
        self.scene.key_up("d")

        self.assertGreater(self.player.x, start_x)
        moved_x = self.player.x
        self.scene.update(1 / 60)
        self.assertEqual(self.player.x, moved_x)

    def test_mouse_motion_updates_world_aim(self):
        self.scene.mouse_move(SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT / 2)
        self.scene.update(1 / 60)

        self.assertAlmostEqual(self.player.aim_angle, 0.0)

    def test_single_click_fires_once_without_shot_miss_text(self):
        self.scene.mouse_down("left")
        self.scene.update(1 / 60)
        self.scene.update(1 / 60)

        self.assertEqual(self.gun.magazine_ammo, 9)
        self.scene.draw(lambda *args: None)
        self.assertFalse(any("SHOT MISS" in call[2] for call in self.hud_font.draw_calls))
        self.scene.mouse_up("left")

    def test_firing_spawns_bullet_from_muzzle_in_aim_direction(self):
        self.scene.bullet_image = FakeImage()
        self.scene.mouse_move(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100)
        self.scene.mouse_down("left")

        self.scene.update(1 / 60)

        bullet = game_world.world[2][0]
        self.assertAlmostEqual(bullet.angle, 3.141592653589793 / 2)
        self.assertAlmostEqual(bullet.x, self.player.x)
        self.assertAlmostEqual(bullet.y, self.player.y + self.player.radius + 14)
        self.scene.draw(lambda *args: None)
        self.assertEqual(self.scene.bullet_image.rotate_calls[0][1:3], (400, 330))

    def test_gun_image_faces_right_without_flipping(self):
        self.scene.gun_image = FakeImage()
        self.scene.mouse_move(SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT / 2 - 50)
        self.scene.update(1 / 60)

        self.scene.draw(lambda *args: None)

        angle, flip = self.scene.gun_image.composite_calls[0][:2]
        self.assertAlmostEqual(angle, 0.4636476090008061)
        self.assertEqual(flip, "")

    def test_gun_image_flips_horizontally_while_aiming_left(self):
        self.scene.gun_image = FakeImage()
        self.scene.mouse_move(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 - 50)
        self.scene.update(1 / 60)

        self.scene.draw(lambda *args: None)

        angle, flip = self.scene.gun_image.composite_calls[0][:2]
        self.assertAlmostEqual(angle, -0.4636476090008061)
        self.assertEqual(flip, "h")
        self.assertTrue(-3.141592653589793 / 2 <= angle <= 3.141592653589793 / 2)

        self.scene.bullet_image = FakeImage()
        self.scene.mouse_down("left")
        self.scene.update(1 / 60)
        bullet = game_world.world[2][0]
        self.assertAlmostEqual(bullet.angle, self.player.aim_angle)
        self.assertLess(bullet.x, self.player.x)
        self.assertGreater(bullet.y, self.player.y)

    def test_mode_toggle_and_empty_click_reload(self):
        self.scene.key_down("e")
        self.assertIs(self.gun.fire_mode, FireMode.AUTO)
        self.gun.magazine_ammo = 0
        self.scene.mouse_down("left")
        self.scene.update(1 / 60)

        self.assertTrue(self.gun.reloading)
        self.assertEqual(self.gun.magazine_ammo, 0)

    def test_f1_toggles_debug_mode_without_resetting_game_or_ammo_state(self):
        self.player.take_damage(25)
        self.gun.magazine_ammo = 3
        self.gun.reserve_ammo = 41
        player_state = (self.player.x, self.player.y, self.player.hp)

        self.scene.key_down("f1")
        self.assertTrue(self.scene.debug_mode)
        self.assertTrue(self.gun.infinite_ammo)
        self.assertEqual(
            (self.player.x, self.player.y, self.player.hp),
            player_state,
        )

        self.scene.mouse_down("left")
        self.scene.update(1 / 60)
        self.assertEqual((self.gun.magazine_ammo, self.gun.reserve_ammo), (3, 41))
        self.scene.mouse_up("left")

        self.scene.key_up("f1")
        self.scene.key_down("f1")
        self.assertFalse(self.scene.debug_mode)
        self.assertFalse(self.gun.infinite_ammo)
        self.assertEqual((self.gun.magazine_ammo, self.gun.reserve_ammo), (3, 41))

    def test_debug_hud_displays_infinite_ammo(self):
        self.gun.infinite_ammo = True

        self.scene.draw(lambda *args: None)

        self.assertIn(
            ((SCREEN_WIDTH - len("AMMO INF") * 10) / 2, 60, "AMMO INF", (255, 255, 255)),
            self.hud_font.draw_calls,
        )

    def test_debug_menu_buttons_spawn_enemy_types_at_map_center(self):
        self.scene.key_down("f1")
        center = (WORLD_WIDTH / 2, WORLD_HEIGHT / 2)

        for index, enemy_type in enumerate(
            (
                EnemyType.BASIC,
                EnemyType.EXPLOSIVE,
                EnemyType.ASSASSIN,
                EnemyType.ARCHER,
                EnemyType.TANKER,
            )
        ):
            screen_y = 42 + index * 30 + 13
            self.scene.mouse_down("left", SCREEN_WIDTH - 50, screen_y)
            enemies = [
                obj
                for layer in game_world.world
                for obj in layer
                if obj is not self.player and hasattr(obj, "stats")
            ]
            self.assertEqual(len(enemies), index + 1)
            self.assertEqual(
                (enemies[-1].x, enemies[-1].y),
                center,
            )
            self.assertEqual(enemies[-1].stats.name, enemy_type.value)
            self.scene.mouse_up("left")

    def test_debug_menu_resets_player_health_and_does_not_fire(self):
        self.scene.key_down("f1")
        self.player.take_damage(35)
        self.scene.mouse_down("left", SCREEN_WIDTH - 50, 42 + 5 * 30 + 13)

        self.assertEqual(self.player.hp, self.player.max_hp)
        self.assertFalse(self.scene.mouse_held)
        self.assertFalse(self.scene._mouse_pressed)
        self.assertEqual(self.gun.magazine_ammo, 10)

    def test_debug_menu_is_rendered_only_in_debug_mode(self):
        self.scene.draw(lambda *args: None)
        self.assertNotIn(
            (DEBUG_MENU_LEFT + 8, SCREEN_HEIGHT - 30, "DEBUG MODE", (255, 220, 80)),
            self.hud_font.draw_calls,
        )

    def test_debug_map_reset_restarts_player_weapon_and_map(self):
        self.scene.key_down("f1")
        self.player.x += 40
        self.player.y -= 25
        self.player.take_damage(30)
        self.gun.magazine_ammo = 2
        self.gun.reserve_ammo = 13
        self.gun.toggle_mode()
        enemy = self.scene.spawn_enemy(
            EnemyType.BASIC,
            self.player.x + 100,
            self.player.y,
        )
        bullet = Bullet(self.player.x, self.player.y, 0, FakeImage())
        game_world.add_object(bullet, depth=2)
        self.scene.show_attack_ranges = True
        self.scene.show_hitboxes = True

        self.scene.mouse_down("left", SCREEN_WIDTH - 50, 42 + 6 * 30 + 13)

        self.assertEqual((self.player.x, self.player.y), self.scene.initial_player_position)
        self.assertEqual(self.player.hp, self.player.max_hp)
        self.assertEqual(
            (self.gun.magazine_ammo, self.gun.reserve_ammo),
            (10, 90),
        )
        self.assertIs(self.gun.fire_mode, FireMode.SINGLE)
        self.assertTrue(self.gun.infinite_ammo)
        self.assertFalse(self.scene.show_attack_ranges)
        self.assertFalse(self.scene.show_hitboxes)
        self.assertNotIn(enemy, [obj for layer in game_world.world for obj in layer])
        self.assertFalse(any(isinstance(obj, Bullet) for layer in game_world.world for obj in layer))
        enemies = [
            obj
            for layer in game_world.world
            for obj in layer
            if hasattr(obj, "stats")
        ]
        self.assertEqual(len(enemies), len(EnemyType))

    def test_debug_visualization_toggles_draw_enemy_hitbox_and_attack_radius(self):
        self.scene.key_down("f1")
        enemy = self.scene.spawn_enemy(
            EnemyType.BASIC,
            self.player.x + 100,
            self.player.y,
        )

        self.scene.mouse_down("left", SCREEN_WIDTH - 50, 42 + 7 * 30 + 13)
        self.scene.mouse_down("left", SCREEN_WIDTH - 50, 42 + 8 * 30 + 13)
        self.scene.draw(lambda *args: None)

        screen_position = self.scene.camera.world_to_screen(enemy.x, enemy.y)
        self.assertIn(
            (*screen_position, round(enemy.radius), 0, 0, 255, 255),
            self.debug_circles,
        )
        self.assertIn(
            (
                *screen_position,
                round(enemy.radius + self.player.radius),
                255,
                0,
                0,
                255,
            ),
            self.debug_circles,
        )
        self.assertTrue(
            all(isinstance(circle[2], int) for circle in self.debug_circles)
        )
        self.assertTrue(self.scene.show_attack_ranges)
        self.assertTrue(self.scene.show_hitboxes)

        self.scene.key_down("f1")
        self.scene.draw(lambda *args: None)
        self.assertIn(
            (DEBUG_MENU_LEFT + 8, SCREEN_HEIGHT - 30, "DEBUG MODE", (255, 220, 80)),
            self.debug_font.draw_calls,
        )
        button_left, _, _, button_bottom = self.scene._debug_button_bounds(0)
        self.assertIn(
            (
                button_left + 6,
                SCREEN_HEIGHT
                - button_bottom
                + (DEBUG_BUTTON_HEIGHT - DEBUG_FONT_SIZE) // 2
                + DEBUG_BUTTON_TEXT_Y_OFFSET,
                "Basic Enemy",
                (255, 255, 255),
            ),
            self.debug_font.draw_calls,
        )

    def test_debug_visualization_marks_assassin_reveal_radius_around_player(self):
        self.scene.key_down("f1")
        self.scene.mouse_down("left", SCREEN_WIDTH - 50, 42 + 9 * 30 + 13)
        self.scene.draw(lambda *args: None)

        self.assertTrue(self.scene.show_assassin_reveal_range)
        player_position = self.scene.camera.world_to_screen(
            self.player.x,
            self.player.y,
        )
        self.assertIn(
            (*player_position, 150, 255, 255, 0, 255),
            self.debug_circles,
        )
        self.assertIn(
            (
                DEBUG_MENU_LEFT + 14,
                SCREEN_HEIGHT
                - (42 + 9 * 30 + 26)
                + (DEBUG_BUTTON_HEIGHT - DEBUG_FONT_SIZE) // 2
                + DEBUG_BUTTON_TEXT_Y_OFFSET,
                "Assassin Reveal: ON",
                (255, 255, 255),
            ),
            self.debug_font.draw_calls,
        )

    def test_r_key_starts_manual_reload(self):
        self.gun.magazine_ammo = 0

        self.scene.key_down("r")

        self.assertTrue(self.gun.reloading)

    def test_draw_renders_background_player_aim_and_hud(self):
        rectangles = []
        self.scene.mouse_move(500, 300)
        self.scene.update(1 / 60)

        def draw_rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
            rectangles.append((x1, y1, x2, y2, r, g, b, a, filled))

        self.scene.draw(draw_rectangle)

        self.assertTrue(self.background.calls)
        self.assertTrue(rectangles)
        self.assertIn((20, 20, 220, 30, 55, 45, 45, 255, True), rectangles)
        self.assertIn((20, 20, 220, 30, 220, 45, 45, 255, True), rectangles)
        self.assertIn((20, 45, "HP 100/100", (255, 255, 255)), self.hud_font.draw_calls)
        self.assertIn(
            (
                (SCREEN_WIDTH - len("AMMO 10/90") * 10) / 2,
                60,
                "AMMO 10/90",
                (255, 255, 255),
            ),
            self.hud_font.draw_calls,
        )
        self.assertIn(
            (
                (SCREEN_WIDTH - len("MODE: SINGLE") * 10) / 2,
                35,
                "MODE: SINGLE",
                (255, 255, 255),
            ),
            self.hud_font.draw_calls,
        )
        self.assertTrue(self.hud_font.draw_calls)

    def test_reload_status_is_centered_at_bottom(self):
        self.gun.magazine_ammo = 0
        self.gun.start_reload()

        self.scene.draw(lambda *args: None)

        self.assertIn(
            (
                (SCREEN_WIDTH - len("RELOAD") * 10) / 2,
                10,
                "RELOAD",
                (255, 255, 255),
            ),
            self.hud_font.draw_calls,
        )

    def test_test_spawn_creates_each_enemy_type_tracking_player(self):
        enemies = self.scene.spawn_test_enemies()

        self.assertEqual(len(enemies), len(EnemyType))
        self.assertTrue(all(enemy.player is self.player for enemy in enemies))
        self.assertEqual(
            {enemy.stats.name for enemy in enemies},
            {enemy_type.value for enemy_type in EnemyType},
        )
        for enemy in enemies:
            start_distance = ((enemy.x - self.player.x) ** 2 + (enemy.y - self.player.y) ** 2) ** 0.5
            enemy.update()
            next_distance = ((enemy.x - self.player.x) ** 2 + (enemy.y - self.player.y) ** 2) ** 0.5
            self.assertLessEqual(next_distance, start_distance)

    def test_scene_removes_defeated_enemies_after_updates(self):
        enemy = self.scene.spawn_enemy(
            EnemyType.BASIC,
            self.player.x + 100,
            self.player.y,
        )
        enemy.take_damage(enemy.max_hp)

        self.scene.update(1 / 60)

        self.assertFalse(any(enemy in layer for layer in game_world.world))

    def test_scene_updates_and_removes_multiple_enemies_safely(self):
        enemies = self.scene.spawn_test_enemies()
        enemies[0].take_damage(enemies[0].max_hp)
        enemies[2].take_damage(enemies[2].max_hp)

        self.scene.update(1 / 60)

        remaining = [
            obj
            for layer in game_world.world
            for obj in layer
            if isinstance(obj, BasicEnemy)
        ]
        self.assertEqual(len(remaining), 0)
        self.assertTrue(all(enemy.is_alive for enemy in enemies[1:2] + enemies[3:]))

    def test_scene_renders_spawned_enemy_with_camera_coordinates(self):
        enemy = self.scene.spawn_enemy(
            EnemyType.BASIC,
            self.player.x + 100,
            self.player.y,
        )
        rectangle_calls = []

        self.scene.draw(lambda *args: rectangle_calls.append(args))

        self.assertTrue(self.enemy_images[EnemyType.BASIC].draw_calls)
        self.assertTrue(rectangle_calls)
        self.assertEqual(
            self.enemy_images[EnemyType.BASIC].draw_calls[0][:2],
            self.scene.camera.world_to_screen(enemy.x, enemy.y),
        )

    def test_scene_skips_rendering_enemies_outside_the_viewport(self):
        visible = self.scene.spawn_enemy(
            EnemyType.BASIC,
            self.player.x + 100,
            self.player.y,
        )
        self.scene.spawn_enemy(
            EnemyType.BASIC,
            WORLD_WIDTH - 20,
            WORLD_HEIGHT - 20,
        )

        self.scene.draw(lambda *args: None)

        image_calls = self.enemy_images[EnemyType.BASIC].draw_calls
        self.assertEqual(len(image_calls), 1)
        self.assertEqual(
            image_calls[0][:2],
            self.scene.camera.world_to_screen(visible.x, visible.y),
        )

    def test_archer_fire_renders_arrow_sprite_in_battle_scene(self):
        archer = self.scene.spawn_enemy(
            EnemyType.ARCHER,
            self.player.x + 220,
            self.player.y,
        )
        self.assertIsInstance(archer, ArcherEnemy)

        charge_duration_frames = round(
            archer.attack_interval * 60 / archer.CHARGE_SPEED_MULTIPLIER
        )
        for _ in range(charge_duration_frames + archer.WARNING_DURATION_FRAMES):
            self.scene.update(1 / 60)

        self.scene.draw(lambda *args: None)
        self.assertTrue(self.scene.arrow_image.rotate_calls)
        arrow = game_world.world[2][0]
        self.assertEqual(arrow.image, self.scene.arrow_image)
        self.assertEqual(
            self.scene.arrow_image.rotate_calls[0][1:3],
            self.scene.camera.world_to_screen(arrow.x, arrow.y),
        )

    def test_spawn_rejects_missing_image_or_draw_function(self):
        self.scene.enemy_images = {}
        with self.assertRaisesRegex(KeyError, "missing image"):
            self.scene.spawn_enemy(EnemyType.BASIC, 0, 0)
        self.scene.enemy_images = self.enemy_images
        self.scene.enemy_draw_rectangle = None
        with self.assertRaisesRegex(RuntimeError, "rectangle drawing"):
            self.scene.spawn_enemy(EnemyType.BASIC, 0, 0)


if __name__ == "__main__":
    unittest.main()
