import math
import unittest

from battle_record import BattleRecord
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
from game_state import GameState
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


class LobbyObstacleTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_player_cannot_walk_through_the_market_stalls(self):
        self.scene.player.x = 300.0
        self.scene.player.y = 440.0
        self.scene.key_down("w")

        for _ in range(120):
            self.scene.update(1.0 / 60)

        self.assertLess(self.scene.player.y, 455.0)
        self.assertFalse(
            self.scene._collides_with_wall(
                self.scene.player.x,
                self.scene.player.y,
            )
        )

    def test_player_slides_along_an_obstacle(self):
        self.scene.player.x = 300.0
        self.scene.player.y = 440.0
        self.scene.key_down("d")

        for _ in range(30):
            self.scene.update(1.0 / 60)

        self.assertGreater(self.scene.player.x, 300.0)
        self.assertAlmostEqual(self.scene.player.y, 440.0, delta=1.0)

    def test_player_cannot_walk_through_the_training_racks(self):
        self.scene.player.x = 1250.0
        self.scene.player.y = 450.0
        self.scene.key_down("w")

        for _ in range(120):
            self.scene.update(1.0 / 60)

        self.assertLess(self.scene.player.y, 495.0)

    def test_player_cannot_walk_through_the_portal_arch(self):
        self.scene.player.x = 900.0
        self.scene.player.y = 600.0
        self.scene.key_down("w")

        for _ in range(120):
            self.scene.update(1.0 / 60)

        self.assertLess(self.scene.player.y, 655.0)

    def test_collision_check_uses_the_player_radius(self):
        self.assertTrue(self.scene._collides_with_wall(68.0, 800.0))
        self.assertFalse(
            self.scene._collides_with_wall(
                68.0 - self.scene.player.radius - 1.0,
                800.0,
            )
        )


class LobbyLocationTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_shop_location_exists(self):
        shop = self.scene.location_at(600.0, 435.0)

        self.assertIsNotNone(shop)
        self.assertEqual(shop.key, "shop")
        self.assertEqual(shop.label, "SHOP")

    def test_nearby_location_is_detected_when_standing_in_the_zone(self):
        self.scene.player.x = 600.0
        self.scene.player.y = 435.0

        self.scene.update(1.0 / 60)

        self.assertIsNotNone(self.scene.nearby_location)
        self.assertEqual(self.scene.nearby_location.key, "shop")

    def test_nearby_location_is_none_away_from_every_zone(self):
        self.scene.player.x = 900.0
        self.scene.player.y = 320.0

        self.scene.update(1.0 / 60)

        self.assertIsNone(self.scene.nearby_location)

    def test_shop_zone_center_is_not_blocked_by_an_obstacle(self):
        self.assertFalse(
            self.scene._collides_with_wall(600.0, 435.0)
        )

    def test_training_location_exists(self):
        training = self.scene.location_at(1500.0, 500.0)

        self.assertIsNotNone(training)
        self.assertEqual(training.key, "training")
        self.assertEqual(training.label, "TRAINING")

    def test_training_zone_center_is_not_blocked_by_an_obstacle(self):
        self.assertFalse(
            self.scene._collides_with_wall(1500.0, 500.0)
        )

    def test_battle_portal_location_exists(self):
        portal = self.scene.location_at(900.0, 620.0)

        self.assertIsNotNone(portal)
        self.assertEqual(portal.key, "portal")
        self.assertEqual(portal.label, "BATTLE PORTAL")

    def test_portal_zone_center_is_not_blocked_by_an_obstacle(self):
        self.assertFalse(
            self.scene._collides_with_wall(900.0, 620.0)
        )


class LobbyRecordsTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.scene = make_scene()
        self.scene.state = self.state

    def tearDown(self):
        self.scene.close()

    def test_records_location_exists_left_of_the_portal(self):
        records = self.scene.location_at(330.0, 435.0)
        portal = self.scene.location_at(900.0, 620.0)

        self.assertIsNotNone(records)
        self.assertEqual(records.key, "records")
        self.assertEqual(records.label, "RECORDS")
        self.assertLess(records.zone_x, portal.zone_x)

    def test_records_zone_center_is_not_blocked_by_an_obstacle(self):
        self.assertFalse(
            self.scene._collides_with_wall(330.0, 435.0)
        )

    def test_entering_the_records_location_opens_the_record_panel(self):
        self.scene.player.x = 330.0
        self.scene.player.y = 435.0
        self.scene.update(1.0 / 60)

        self.scene.key_down("return")

        self.assertEqual(self.scene.panel, "records")

    def test_record_panel_can_be_closed(self):
        self.scene.open_records()

        self.scene.key_down("return")

        self.assertIsNone(self.scene.panel)

    def test_record_panel_lists_the_stored_records(self):
        self.state.add_record(
            BattleRecord(
                result="defeat",
                reached_wave=7,
                elapsed_time=125.5,
            )
        )
        self.scene.open_records()

        drawn = []
        self.scene.draw(
            lambda *args: drawn.append(args),
        )

        self.assertTrue(drawn)

    def test_game_state_keeps_the_newest_record_first(self):
        self.state.add_record(
            BattleRecord(result="defeat", reached_wave=3, elapsed_time=60.0)
        )
        self.state.add_record(
            BattleRecord(result="victory", reached_wave=30, elapsed_time=900.0)
        )

        self.assertEqual(self.state.records[0].result, "victory")
        self.assertEqual(len(self.state.records), 2)
