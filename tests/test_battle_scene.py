import unittest

import game_world
from battle_scene import BattleScene
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


class FakeBackground:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class BattleSceneTests(unittest.TestCase):
    def setUp(self):
        self.player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=FakeImage(),
        )
        self.gun = Gun()
        self.background = FakeBackground()
        self.scene = BattleScene(self.player, self.gun, self.background)

    def tearDown(self):
        self.scene.close()

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

    def test_single_click_fires_once_and_shows_result(self):
        self.scene.mouse_down("left")
        self.scene.update(1 / 60)
        self.scene.update(1 / 60)

        self.assertEqual(self.gun.magazine_ammo, 9)
        self.assertEqual(self.scene.last_shot_result.value, "miss")
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
        self.scene.draw(lambda *args: None, lambda *args: None)
        self.assertEqual(self.scene.bullet_image.rotate_calls[0][1:3], (400, 330))

    def test_gun_image_faces_right_without_flipping(self):
        self.scene.gun_image = FakeImage()
        self.scene.mouse_move(SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT / 2 - 50)
        self.scene.update(1 / 60)

        self.scene.draw(lambda *args: None, lambda *args: None)

        angle, flip = self.scene.gun_image.composite_calls[0][:2]
        self.assertAlmostEqual(angle, 0.4636476090008061)
        self.assertEqual(flip, "")

    def test_gun_image_flips_horizontally_while_aiming_left(self):
        self.scene.gun_image = FakeImage()
        self.scene.mouse_move(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 - 50)
        self.scene.update(1 / 60)

        self.scene.draw(lambda *args: None, lambda *args: None)

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
        lines = []
        rectangles = []
        self.scene.mouse_move(500, 300)
        self.scene.update(1 / 60)

        def draw_rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
            rectangles.append((x1, y1, x2, y2, r, g, b, a, filled))

        def draw_line(x1, y1, x2, y2, r=0, g=0, b=0, a=255):
            lines.append((x1, y1, x2, y2, r, g, b, a))

        self.scene.draw(
            draw_rectangle,
            draw_line,
        )

        self.assertTrue(self.background.calls)
        self.assertTrue(rectangles)
        self.assertTrue(lines)
        self.assertIn((20, 570, 220, 580, 55, 45, 45, 255, True), rectangles)
        self.assertIn((20, 570, 220, 580, 220, 45, 45, 255, True), rectangles)
        self.assertTrue(any(line[-3:] == (255, 255, 255) for line in lines))


if __name__ == "__main__":
    unittest.main()
