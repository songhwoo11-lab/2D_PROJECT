import unittest

from battle_scene import BattleScene
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from player import Player
from weapon import FireMode, Gun


class FakeImage:
    def draw(self, *args):
        pass


class FakeBackground:
    def __init__(self):
        self.calls = []

    def draw(self, *args):
        self.calls.append(args)


class BattleSceneTests(unittest.TestCase):
    def setUp(self):
        self.player = Player(
            SCREEN_WIDTH * 2,
            SCREEN_HEIGHT * 2,
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
        colors = []
        self.scene.mouse_move(500, 300)
        self.scene.update(1 / 60)

        self.scene.draw(
            lambda *line: lines.append(line),
            lambda *rect: rectangles.append(rect),
            lambda *color: colors.append(color),
        )

        self.assertTrue(self.background.calls)
        self.assertTrue(lines)
        self.assertTrue(rectangles)
        self.assertIn((255, 255, 255), colors)


if __name__ == "__main__":
    unittest.main()
