import unittest

from game_config import (
    LOBBY_BOUNDS_BOTTOM,
    LOBBY_BOUNDS_LEFT,
    LOBBY_BOUNDS_RIGHT,
    LOBBY_BOUNDS_TOP,
    LOBBY_PLAYER_START_X,
    LOBBY_PLAYER_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from lobby_scene import LobbyScene
from player import Player


def make_scene():
    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    return LobbyScene(player)


class LobbySceneLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_scene_starts_without_a_pending_action(self):
        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)

    def test_update_runs_without_error(self):
        self.scene.update(1.0 / 60)

    def test_draw_runs_without_error(self):
        calls = []

        self.scene.draw(lambda *args: calls.append(args))

        self.assertEqual(calls, [])

    def test_key_down_and_up_track_pressed_keys(self):
        self.scene.key_down("w")
        self.assertIn("w", self.scene.keys)

        self.scene.key_up("w")
        self.assertNotIn("w", self.scene.keys)

    def test_mouse_move_tracks_the_cursor(self):
        self.scene.mouse_move(120, 340)

        self.assertEqual(self.scene.mouse_screen_x, 120)
        self.assertEqual(self.scene.mouse_screen_y, 340)


class LobbyBoundsTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_player_starts_at_the_lobby_entrance(self):
        self.assertEqual(self.scene.player.x, LOBBY_PLAYER_START_X)
        self.assertEqual(self.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_player_cannot_leave_the_left_bound(self):
        self.scene.player.x = LOBBY_BOUNDS_LEFT - 500.0

        self.scene.update(1.0 / 60)

        self.assertAlmostEqual(
            self.scene.player.x,
            LOBBY_BOUNDS_LEFT + self.scene.player.radius,
        )

    def test_player_cannot_leave_the_right_bound(self):
        self.scene.player.x = LOBBY_BOUNDS_RIGHT + 500.0

        self.scene.update(1.0 / 60)

        self.assertAlmostEqual(
            self.scene.player.x,
            LOBBY_BOUNDS_RIGHT - self.scene.player.radius,
        )

    def test_player_cannot_leave_the_bottom_bound(self):
        self.scene.player.y = LOBBY_BOUNDS_BOTTOM - 500.0

        self.scene.update(1.0 / 60)

        self.assertAlmostEqual(
            self.scene.player.y,
            LOBBY_BOUNDS_BOTTOM + self.scene.player.radius,
        )

    def test_player_cannot_leave_the_top_bound(self):
        self.scene.player.y = LOBBY_BOUNDS_TOP + 500.0

        self.scene.update(1.0 / 60)

        self.assertAlmostEqual(
            self.scene.player.y,
            LOBBY_BOUNDS_TOP - self.scene.player.radius,
        )

    def test_reset_player_position_returns_to_the_entrance(self):
        self.scene.player.x = 200.0
        self.scene.player.y = 700.0

        self.scene.reset_player_position()

        self.assertEqual(self.scene.player.x, LOBBY_PLAYER_START_X)
        self.assertEqual(self.scene.player.y, LOBBY_PLAYER_START_Y)
