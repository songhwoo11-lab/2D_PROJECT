import unittest
from unittest.mock import patch

import game_world
from battle_scene import BattleScene
from enemy import EnemyType
from enemy_types import BasicEnemy
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
        self.scene = BattleScene(
            self.player,
            self.gun,
            self.background,
            hud_font=self.hud_font,
        )
        self.enemy_images = {
            enemy_type: FakeImage() for enemy_type in EnemyType
        }
        self.scene.enemy_images = self.enemy_images
        self.scene.enemy_draw_rectangle = lambda *args: None

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
