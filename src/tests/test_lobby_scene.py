import unittest
from unittest.mock import MagicMock, patch

from battle_record import BattleRecord
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from game_state import GameState
from lobby_map import (
    LOBBY_LOCATIONS,
    LOBBY_NODE_BY_KEY,
    LOBBY_START_KEY,
)
from lobby_scene import LobbyScene
from player import Player


def make_scene():
    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    return LobbyScene(player)


def press(scene, key):
    scene.key_down(key)
    scene.key_up(key)


class LobbySceneLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_scene_starts_at_the_center_without_a_pending_action(self):
        self.assertEqual(self.scene.current_node, LOBBY_START_KEY)
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


class LobbyFixedPositionTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_player_starts_at_the_center_node(self):
        center = LOBBY_NODE_BY_KEY["center"]

        self.assertEqual(self.scene.player.x, center.zone_x)
        self.assertEqual(self.scene.player.y, center.zone_y)
        self.assertEqual(self.scene.nearby_location.key, "center")

    def test_reset_player_position_returns_to_the_center(self):
        press(self.scene, "d")
        self.assertEqual(self.scene.current_node, "training")

        self.scene.reset_player_position()

        center = LOBBY_NODE_BY_KEY["center"]
        self.assertEqual(self.scene.current_node, "center")
        self.assertEqual(self.scene.player.x, center.zone_x)
        self.assertEqual(self.scene.player.y, center.zone_y)

    def test_update_does_not_move_the_player(self):
        self.scene.update(0.5)

        center = LOBBY_NODE_BY_KEY["center"]
        self.assertEqual(self.scene.player.x, center.zone_x)
        self.assertEqual(self.scene.player.y, center.zone_y)

    def test_unmapped_direction_keeps_the_current_node(self):
        press(self.scene, "a")
        press(self.scene, "a")
        self.assertEqual(self.scene.current_node, "shop")

        press(self.scene, "a")

        self.assertEqual(self.scene.current_node, "shop")
        shop = LOBBY_NODE_BY_KEY["shop"]
        self.assertEqual(self.scene.player.x, shop.zone_x)
        self.assertEqual(self.scene.player.y, shop.zone_y)


class LobbyMovementGraphTests(unittest.TestCase):
    def tearDown(self):
        self.scene.close()

    def _move(self, *keys):
        self.scene = make_scene()
        for key in keys:
            press(self.scene, key)

    def test_shop_to_records_uses_d(self):
        self._move("a", "a", "d")

        self.assertEqual(self.scene.current_node, "records")

    def test_records_to_center_uses_d(self):
        self._move("a", "d")

        self.assertEqual(self.scene.current_node, "center")

    def test_records_to_shop_uses_a(self):
        self._move("a", "a")

        self.assertEqual(self.scene.current_node, "shop")

    def test_center_to_records_uses_a(self):
        self._move("a")

        self.assertEqual(self.scene.current_node, "records")

    def test_center_to_stairs_uses_s(self):
        self._move("s")

        self.assertEqual(self.scene.current_node, "stairs")

    def test_center_to_training_uses_d(self):
        self._move("d")

        self.assertEqual(self.scene.current_node, "training")

    def test_center_to_portal_uses_w(self):
        self._move("w")

        self.assertEqual(self.scene.current_node, "portal")

    def test_training_to_center_uses_a(self):
        self._move("d", "a")

        self.assertEqual(self.scene.current_node, "center")

    def test_portal_to_center_uses_s(self):
        self._move("w", "s")

        self.assertEqual(self.scene.current_node, "center")

    def test_stairs_to_center_uses_w(self):
        self._move("s", "w")

        self.assertEqual(self.scene.current_node, "center")

    def test_every_move_places_the_player_at_the_fixed_node(self):
        self._move("s")
        stairs = LOBBY_NODE_BY_KEY["stairs"]

        self.assertEqual(self.scene.player.x, stairs.zone_x)
        self.assertEqual(self.scene.player.y, stairs.zone_y)
        self.assertEqual(self.scene.nearby_location.key, "stairs")


class LobbyLocationTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.scene = make_scene()
        self.scene.state = self.state

    def tearDown(self):
        self.scene.close()

    def test_every_fixed_location_exists(self):
        keys = [location.key for location in self.scene.locations]

        for key in ("shop", "records", "center", "portal", "training", "stairs"):
            self.assertIn(key, keys)

    def test_location_at_finds_a_fixed_node(self):
        shop = LOBBY_NODE_BY_KEY["shop"]

        location = self.scene.location_at(shop.zone_x, shop.zone_y)

        self.assertIsNotNone(location)
        self.assertEqual(location.key, "shop")

    def test_enter_at_the_center_does_nothing(self):
        press(self.scene, "return")

        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)
        self.assertIsNone(self.scene.panel)

    def test_enter_at_the_shop_requests_the_shop_scene(self):
        press(self.scene, "a")
        press(self.scene, "a")

        press(self.scene, "return")

        self.assertEqual(self.scene.pending_action, "enter_shop")

    def test_enter_at_the_training_ground_requests_the_training_scene(self):
        press(self.scene, "d")

        press(self.scene, "return")

        self.assertEqual(self.scene.pending_action, "enter_training")

    def test_enter_at_the_portal_starts_the_battle(self):
        press(self.scene, "w")

        press(self.scene, "return")

        self.assertEqual(self.scene.pending_action, "start_battle")

    def test_enter_at_records_opens_the_record_panel(self):
        press(self.scene, "a")

        press(self.scene, "return")

        self.assertEqual(self.scene.panel, "records")

    def test_record_panel_can_be_closed(self):
        self.scene.open_records()

        press(self.scene, "return")

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
        self.scene.draw(lambda *args: drawn.append(args))

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


class LobbyGuiTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_access_guide_is_shown_at_the_current_node(self):
        press(self.scene, "a")
        self.scene.update(1.0 / 60)

        self.assertEqual(self.scene.nearby_location.key, "records")

    def test_every_fixed_place_has_a_label(self):
        labels = [location.label for location in LOBBY_LOCATIONS]

        self.assertIn("SHOP", labels)
        self.assertIn("RECORDS", labels)
        self.assertIn("CENTER", labels)
        self.assertIn("BATTLE PORTAL", labels)
        self.assertIn("TRAINING", labels)
        self.assertIn("EXIT STAIRS", labels)

    def test_only_the_current_location_name_is_drawn(self):
        self.scene.hud_font = MagicMock()
        press(self.scene, "a")

        with patch("lobby_scene.draw_text_at_center") as draw_at_center, patch(
            "lobby_scene.draw_centered_text"
        ) as draw_centered:
            self.scene.draw(lambda *args: None)

        labels = [call.args[3] for call in draw_at_center.call_args_list]
        self.assertEqual(labels, ["RECORDS"])
        draw_centered.assert_not_called()

    def test_draw_does_not_render_a_location_marker(self):
        press(self.scene, "a")
        self.scene.update(1.0 / 60)

        calls = []
        self.scene.draw(lambda *args: calls.append(args))

        self.assertEqual(calls, [])


class LobbyPortalEntryTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.scene = make_scene()
        self.scene.state = self.state

    def tearDown(self):
        self.scene.close()

    def test_one_owned_gun_does_not_need_a_selection_screen(self):
        self.assertFalse(self.state.needs_gun_selection())

    def test_two_owned_guns_need_a_selection_screen(self):
        self.state.owned_guns = ["pistol", "rifle"]

        self.assertTrue(self.state.needs_gun_selection())

    def test_two_owned_guns_request_the_selection_screen(self):
        self.state.owned_guns = ["pistol", "rifle"]
        press(self.scene, "w")

        press(self.scene, "return")

        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

    def test_gun_selection_moves_between_the_owned_guns(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()

        press(self.scene, "s")

        self.assertEqual(self.scene.gun_selection_index, 1)

    def test_gun_selection_wraps_around(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()

        press(self.scene, "w")

        self.assertEqual(self.scene.gun_selection_index, 1)

    def test_confirming_the_gun_selection_starts_the_battle(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "s")

        press(self.scene, "return")

        self.assertEqual(self.state.selected_gun, "rifle")
        self.assertIsNone(self.scene.panel)
        self.assertEqual(self.scene.pending_action, "start_battle")

    def test_cancelling_the_gun_selection_keeps_the_previous_gun(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "s")

        press(self.scene, "q")

        self.assertEqual(self.state.selected_gun, "pistol")
        self.assertIsNone(self.scene.panel)
        self.assertIsNone(self.scene.pending_action)


class LobbyStairsExitTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene()

    def tearDown(self):
        self.scene.close()

    def test_moving_to_the_stairs_does_not_exit_by_itself(self):
        press(self.scene, "s")

        self.assertEqual(self.scene.current_node, "stairs")
        self.assertFalse(self.scene.exit_requested)

    def test_enter_at_the_stairs_requests_the_game_exit(self):
        press(self.scene, "s")

        press(self.scene, "return")

        self.assertTrue(self.scene.exit_requested)
