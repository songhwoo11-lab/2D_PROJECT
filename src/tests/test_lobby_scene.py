import math
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


class LobbyMovementTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()
        self.scene.player.x = LOBBY_PLAYER_START_X
        self.scene.player.y = LOBBY_PLAYER_START_Y

    def tearDown(self):
        self.scene.close()

    def test_player_stays_put_without_input(self):
        self.scene.update(1.0 / 60)

        self.assertAlmostEqual(self.scene.player.x, LOBBY_PLAYER_START_X)
        self.assertAlmostEqual(self.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_right_key_moves_the_player_right(self):
        self.scene.key_down("d")

        self.scene.update(0.5)

        self.assertGreater(self.scene.player.x, LOBBY_PLAYER_START_X)
        self.assertAlmostEqual(self.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_left_key_moves_the_player_left(self):
        self.scene.key_down("a")

        self.scene.update(0.5)

        self.assertLess(self.scene.player.x, LOBBY_PLAYER_START_X)

    def test_up_key_moves_the_player_up(self):
        self.scene.key_down("w")

        self.scene.update(0.5)

        self.assertGreater(self.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_down_key_moves_the_player_down(self):
        self.scene.key_down("s")

        self.scene.update(0.5)

        self.assertLess(self.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_released_key_stops_the_movement(self):
        self.scene.key_down("d")
        self.scene.update(0.5)
        moved_x = self.scene.player.x
        self.scene.key_up("d")

        self.scene.update(0.5)

        self.assertAlmostEqual(self.scene.player.x, moved_x)

    def test_diagonal_movement_is_not_faster(self):
        self.scene.key_down("d")
        self.scene.key_down("w")
        diagonal_scene = make_scene()
        diagonal_scene.key_down("d")
        diagonal_scene.update(0.5)

        self.scene.update(0.5)

        diagonal_distance = math.hypot(
            self.scene.player.x - LOBBY_PLAYER_START_X,
            self.scene.player.y - LOBBY_PLAYER_START_Y,
        )
        straight_distance = math.hypot(
            diagonal_scene.player.x - LOBBY_PLAYER_START_X,
            diagonal_scene.player.y - LOBBY_PLAYER_START_Y,
        )
        self.assertAlmostEqual(diagonal_distance, straight_distance)
        diagonal_scene.close()
