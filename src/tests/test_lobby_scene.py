import math
import unittest
from unittest.mock import MagicMock, call, patch

from battle_record import BattleRecord, TrainingRecord
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from game_state import GameState
from lobby_map import (
    LOBBY_LOCATIONS,
    LOBBY_NODE_BY_KEY,
    LOBBY_START_KEY,
)
from lobby_scene import (
    GUN_SELECT_HOVER_OUTLINE_COLOR,
    GUN_SELECT_IMAGE_SIZES,
    GUN_SELECT_IMAGE_Y,
    GUN_SELECT_LOCKED_OPACITY,
    GUN_SELECT_LOCK_COLOR,
    GUN_SELECT_LOCK_KEYHOLE_COLOR,
    GUN_SELECT_SELECTED_SLOT_SIZE,
    GUN_SELECT_STATE_DISABLED_COLOR,
    GUN_SELECT_STATE_DISABLED_TEXT_COLOR,
    GUN_SELECT_UNSELECTED_SLOT_SIZE,
    LobbyScene,
    PORTAL_ENTRY_SECONDS,
    PORTAL_ENTRY_TOTAL_ROTATIONS,
    RECORDS_BOOK_HEIGHT,
    RECORDS_BOOK_PAPER_BOTTOM_IMAGE_Y,
    RECORDS_BOOK_PAPER_TOP_IMAGE_Y,
    gun_select_card_rect,
    gun_select_exit_button_rect,
    gun_select_state_button_rect,
    records_exit_button_rect,
)
from player import Player
from shop import GUN_SHOP_ORDER


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

    def test_draw_shows_direction_arrows_outside_the_portal_animation(self):
        with patch.object(self.scene, "_draw_direction_arrows") as draw_arrows:
            self.scene.draw(lambda *args: None)

        draw_arrows.assert_called_once_with()

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
        press(self.scene, "space")

        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)
        self.assertIsNone(self.scene.panel)

    def test_enter_at_the_shop_requests_the_shop_scene(self):
        press(self.scene, "a")
        press(self.scene, "a")

        press(self.scene, "space")

        self.assertEqual(self.scene.pending_action, "enter_shop")

    def test_enter_at_the_training_ground_requests_the_training_scene(self):
        press(self.scene, "d")

        press(self.scene, "space")

        self.assertEqual(self.scene.pending_action, "enter_training")

    def test_enter_at_the_portal_opens_the_gun_selection_before_the_battle(self):
        press(self.scene, "w")

        press(self.scene, "space")

        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

        press(self.scene, "space")

        self.assertTrue(self.scene.portal_entry_active)
        self.assertIsNone(self.scene.pending_action)

    def test_enter_at_records_opens_the_record_panel(self):
        press(self.scene, "a")

        press(self.scene, "space")

        self.assertEqual(self.scene.panel, "records")

    def test_record_panel_can_be_closed_with_q(self):
        self.scene.open_records()

        press(self.scene, "q")

        self.assertIsNone(self.scene.panel)

    def test_space_does_not_close_the_record_panel(self):
        self.scene.open_records()

        press(self.scene, "space")

        self.assertEqual(self.scene.panel, "records")

    def test_escape_closes_the_record_panel(self):
        self.scene.open_records()

        press(self.scene, "escape")

        self.assertIsNone(self.scene.panel)
        self.assertFalse(self.scene.exit_requested)

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
        self.assertIn("EXIT GAME", labels)

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

    def test_one_owned_gun_needs_a_selection_screen(self):
        self.assertTrue(self.state.needs_gun_selection())

    def test_two_owned_guns_need_a_selection_screen(self):
        self.state.owned_guns = ["pistol", "rifle"]

        self.assertTrue(self.state.needs_gun_selection())

    def test_two_owned_guns_request_the_selection_screen(self):
        self.state.owned_guns = ["pistol", "rifle"]
        press(self.scene, "w")

        press(self.scene, "space")

        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

    def test_one_owned_gun_requests_the_selection_screen(self):
        press(self.scene, "w")

        press(self.scene, "space")

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

    def test_confirming_the_gun_selection_starts_the_portal_entry_animation(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "s")

        press(self.scene, "space")

        self.assertEqual(self.state.selected_gun, "rifle")
        self.assertIsNone(self.scene.panel)
        self.assertTrue(self.scene.portal_entry_active)
        self.assertIsNone(self.scene.pending_action)

    def test_portal_entry_moves_spins_and_fades_the_player_over_three_seconds(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "space")
        start_x = self.scene.player.x
        start_y = self.scene.player.y

        self.scene.update(PORTAL_ENTRY_SECONDS / 2)

        self.assertTrue(self.scene.portal_entry_active)
        self.assertAlmostEqual(self.scene.player.x, start_x)
        self.assertGreater(self.scene.player.y, start_y)
        self.assertAlmostEqual(self.scene.portal_entry_opacity, 0.5)
        self.assertAlmostEqual(
            self.scene.portal_entry_angle,
            math.pi * PORTAL_ENTRY_TOTAL_ROTATIONS,
        )
        self.assertIsNone(self.scene.pending_action)

        self.scene.update(PORTAL_ENTRY_SECONDS / 2)

        self.assertFalse(self.scene.portal_entry_active)
        self.assertAlmostEqual(self.scene.portal_entry_opacity, 0.0)
        self.assertAlmostEqual(
            self.scene.portal_entry_angle,
            math.tau * PORTAL_ENTRY_TOTAL_ROTATIONS,
        )
        self.assertEqual(self.scene.pending_action, "battle_entry_loading")

    def test_portal_entry_draws_the_player_with_spin_and_transparency(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "space")
        self.scene.update(1.0)
        self.scene.player.image = object()
        self.scene.player.draw = MagicMock()

        self.scene.draw(lambda *args: None)

        self.scene.player.draw.assert_called_once_with(
            angle=self.scene.portal_entry_angle,
            opacity=self.scene.portal_entry_opacity,
        )

    def test_portal_entry_hides_the_direction_arrows(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "space")

        with patch.object(self.scene, "_draw_direction_arrows") as draw_arrows:
            self.scene.draw(lambda *args: None)

        draw_arrows.assert_not_called()

    def test_portal_entry_ignores_input_until_the_animation_finishes(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "space")

        press(self.scene, "a")
        self.scene.mouse_down("left", 10, 10)

        self.assertEqual(self.scene.current_node, "center")
        self.assertIsNone(self.scene.panel)
        self.assertTrue(self.scene.portal_entry_active)

    def test_escape_cancels_the_gun_selection_and_keeps_the_previous_gun(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "s")

        press(self.scene, "escape")

        self.assertEqual(self.state.selected_gun, "pistol")
        self.assertIsNone(self.scene.panel)
        self.assertIsNone(self.scene.pending_action)

    def test_q_no_longer_cancels_the_gun_selection(self):
        self.state.owned_guns = ["pistol", "rifle"]
        self.scene.open_gun_selection()
        press(self.scene, "s")

        press(self.scene, "q")

        self.assertEqual(self.scene.panel, "gun_select")
        self.assertEqual(self.scene.gun_selection_index, 1)


class LobbyGunSelectCardTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(owned_guns=["pistol", "rifle"])
        self.scene = make_scene()
        self.scene.state = self.state
        self.scene.hud_font = MagicMock()
        self.scene.open_gun_selection()

    def tearDown(self):
        self.scene.close()

    def hover_rect(self, rect):
        left, bottom, right, top = rect
        self.scene.mouse_move(
            (left + right) / 2, SCREEN_HEIGHT - (bottom + top) / 2
        )

    def click_rect(self, rect):
        self.hover_rect(rect)
        left, bottom, right, top = rect
        self.scene.mouse_down("left", (left + right) / 2, SCREEN_HEIGHT - (bottom + top) / 2)

    def test_draw_shows_three_cards_with_state_buttons(self):
        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: rectangles.append(args))

        labels = [call.args[3] for call in text_draw.call_args_list]
        self.assertEqual(labels.count("State"), 3)
        card_rects = [tuple(gun_select_card_rect(index)) for index in range(3)]
        drawn_rects = {tuple(args[:4]) for args in rectangles}
        for card in card_rects:
            self.assertIn(card, drawn_rects)

    def test_gun_selection_does_not_show_bottom_key_hints(self):
        with patch("lobby_scene.draw_centered_text") as centered_text, patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: None)

        labels = [call.args[2] for call in centered_text.call_args_list]
        self.assertFalse(
            any(
                "CLICK GUN" in label
                or "W/S + SPACE" in label
                or "Q : CANCEL" in label
                for label in labels
            )
        )

    def test_state_button_is_raised_twenty_pixels_and_keeps_its_size(self):
        left, bottom, right, top = gun_select_state_button_rect(0)
        card_left = gun_select_card_rect(0)[0]

        self.assertEqual(left, card_left + 28)
        self.assertEqual((bottom, top), (352, 437))
        self.assertEqual(right - left, 415)
        self.assertEqual(top - bottom, 85)

        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: None)

        state_labels = [
            call for call in text_draw.call_args_list if call.args[3] == "State"
        ]
        self.assertEqual(len(state_labels), 3)
        for label in state_labels:
            self.assertEqual(label.args[2], 394)

    def test_exit_button_is_in_the_bottom_right(self):
        left, bottom, right, top = gun_select_exit_button_rect()

        self.assertGreater(left, SCREEN_WIDTH / 2)
        self.assertLess(top, SCREEN_HEIGHT / 4)
        self.assertEqual(right, SCREEN_WIDTH - 60)
        self.assertGreater(bottom, 0)

    def test_exit_button_is_drawn_with_its_label(self):
        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: rectangles.append(args))

        labels = [call.args[3] for call in text_draw.call_args_list]
        drawn_rects = {tuple(args[:4]) for args in rectangles}
        self.assertIn("EXIT", labels)
        self.assertIn(tuple(gun_select_exit_button_rect()), drawn_rects)

    def test_hovering_exit_button_sets_the_exit_target(self):
        self.hover_rect(gun_select_exit_button_rect())

        self.assertEqual(self.scene.gun_select_hover_target, ("exit", None))

    def test_clicking_exit_button_returns_to_the_lobby(self):
        self.scene.gun_state_panel_gun_id = "pistol"

        self.click_rect(gun_select_exit_button_rect())

        self.assertIsNone(self.scene.panel)
        self.assertIsNone(self.scene.gun_state_panel_gun_id)
        self.assertIsNone(self.scene.pending_action)
        self.assertEqual(self.state.selected_gun, "pistol")

    def test_lock_color_is_dark_gray(self):
        self.assertEqual(GUN_SELECT_LOCK_COLOR, (85, 85, 90, 255))

    def test_hover_activates_the_owned_card_under_the_cursor(self):
        index = GUN_SHOP_ORDER.index("rifle")
        card = gun_select_card_rect(index)
        self.hover_rect(card)

        self.assertEqual(self.scene.gun_select_hover_index, index)
        self.assertEqual(
            self.scene.gun_selection_index, self.state.owned_guns.index("rifle")
        )

        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: rectangles.append(args))

        outline = tuple(card) + GUN_SELECT_HOVER_OUTLINE_COLOR + (False,)
        self.assertIn(outline, [tuple(args) for args in rectangles])

    def test_hover_activates_a_locked_card_without_changing_the_selection(self):
        index = GUN_SHOP_ORDER.index("machine_gun")
        card = gun_select_card_rect(index)
        self.hover_rect(card)

        self.assertEqual(self.scene.gun_select_hover_index, index)
        self.assertEqual(self.scene.gun_selection_index, 0)

        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: rectangles.append(args))

        outline = tuple(card) + GUN_SELECT_HOVER_OUTLINE_COLOR + (False,)
        self.assertIn(outline, [tuple(args) for args in rectangles])

    def test_clicking_an_owned_gun_only_marks_it_as_selected(self):
        self.click_rect(gun_select_card_rect(GUN_SHOP_ORDER.index("rifle")))

        self.assertEqual(self.scene.gun_select_pending_gun_id, "rifle")
        self.assertEqual(self.state.selected_gun, "pistol")
        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

    def test_clicking_the_marked_gun_starts_the_battle(self):
        rect = gun_select_card_rect(GUN_SHOP_ORDER.index("rifle"))
        self.click_rect(rect)
        self.click_rect(rect)

        self.assertEqual(self.state.selected_gun, "rifle")
        self.assertIsNone(self.scene.panel)
        self.assertTrue(self.scene.portal_entry_active)
        self.assertIsNone(self.scene.pending_action)

    def test_clicking_a_different_gun_moves_the_mark(self):
        self.click_rect(gun_select_card_rect(GUN_SHOP_ORDER.index("rifle")))
        self.click_rect(gun_select_card_rect(GUN_SHOP_ORDER.index("pistol")))

        self.assertEqual(self.scene.gun_select_pending_gun_id, "pistol")
        self.assertEqual(self.state.selected_gun, "pistol")
        self.assertIsNone(self.scene.pending_action)

    def test_clicking_a_locked_gun_does_not_change_the_selection(self):
        self.click_rect(gun_select_card_rect(GUN_SHOP_ORDER.index("machine_gun")))

        self.assertEqual(self.state.selected_gun, "pistol")
        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

    def test_state_button_opens_the_state_panel_without_starting_the_battle(self):
        self.click_rect(gun_select_state_button_rect(GUN_SHOP_ORDER.index("pistol")))

        self.assertEqual(self.scene.gun_state_panel_gun_id, "pistol")
        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: None)

        labels = [call.args[3] for call in text_draw.call_args_list]
        self.assertIn("STATE - PISTOL", labels)
        self.assertFalse(
            any(label.startswith("STARTING AMMO") for label in labels)
        )

    def test_locked_gun_state_button_does_not_open_the_state_panel(self):
        self.click_rect(gun_select_state_button_rect(GUN_SHOP_ORDER.index("machine_gun")))

        self.assertIsNone(self.scene.gun_state_panel_gun_id)
        self.assertEqual(self.scene.panel, "gun_select")
        self.assertIsNone(self.scene.pending_action)

    def test_locked_gun_state_button_is_drawn_as_disabled(self):
        index = GUN_SHOP_ORDER.index("machine_gun")
        button_rect = tuple(gun_select_state_button_rect(index))
        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: rectangles.append(args))

        disabled_button = button_rect + GUN_SELECT_STATE_DISABLED_COLOR + (255, True)
        self.assertIn(disabled_button, [tuple(args) for args in rectangles])

        center_x = (button_rect[0] + button_rect[2]) / 2
        state_labels = [
            call
            for call in text_draw.call_args_list
            if call.args[3] == "State" and call.args[1] == center_x
        ]
        self.assertEqual(len(state_labels), 1)
        self.assertEqual(
            state_labels[0].args[4], GUN_SELECT_STATE_DISABLED_TEXT_COLOR
        )

    def test_locked_gun_image_is_translucent(self):
        image = MagicMock()
        self.scene.gun_images = {"machine_gun": image}
        width, height = GUN_SELECT_IMAGE_SIZES["machine_gun"]
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: None)

        image.draw.assert_called_once_with(
            self._machine_gun_center_x(),
            GUN_SELECT_IMAGE_Y,
            width,
            height,
        )
        self.assertEqual(
            image.opacify.call_args_list,
            [call(GUN_SELECT_LOCKED_OPACITY), call(1.0)],
        )

    def test_locked_gun_draws_a_lock_shape_over_the_image(self):
        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: rectangles.append(args))

        lock_rectangles = [
            args
            for args in rectangles
            if tuple(args[4:8]) == GUN_SELECT_LOCK_COLOR and args[8] is True
        ]
        keyhole_rectangles = [
            args
            for args in rectangles
            if tuple(args[4:8]) == GUN_SELECT_LOCK_KEYHOLE_COLOR and args[8] is True
        ]
        self.assertEqual(len(lock_rectangles), 4)
        self.assertEqual(len(keyhole_rectangles), 1)

    def _machine_gun_center_x(self):
        left, bottom, right, top = gun_select_card_rect(
            GUN_SHOP_ORDER.index("machine_gun")
        )
        return (left + right) / 2


class LobbyGunSelectImageTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(owned_guns=["pistol", "rifle"])
        self.background = MagicMock()
        self.selected = MagicMock()
        self.unselected = MagicMock()
        self.scene = LobbyScene(
            Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
            hud_font=MagicMock(),
            state=self.state,
            gun_select_background=self.background,
            selected_slot_image=self.selected,
            unselected_slot_image=self.unselected,
        )
        self.scene.open_gun_selection()

    def tearDown(self):
        self.scene.close()

    def draw_scene(self, rectangles=None):
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(
                lambda *args: rectangles.append(args)
                if rectangles is not None
                else None
            )

    def center_of(self, index):
        rect = gun_select_card_rect(index)
        return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2

    def test_draws_the_gun_select_background_image(self):
        self.draw_scene()

        self.background.draw.assert_called_once_with(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )

    def test_draws_selected_and_unselected_slot_images(self):
        self.draw_scene()

        selected_index = GUN_SHOP_ORDER.index("pistol")
        self.selected.draw.assert_called_once_with(
            *self.center_of(selected_index), *GUN_SELECT_SELECTED_SLOT_SIZE
        )
        self.assertEqual(self.unselected.draw.call_count, 2)
        expected_calls = [
            call(*self.center_of(index), *GUN_SELECT_UNSELECTED_SLOT_SIZE)
            for index, gun_id in enumerate(GUN_SHOP_ORDER)
            if gun_id != "pistol"
        ]
        self.assertEqual(self.unselected.draw.call_args_list, expected_calls)

    def test_slot_images_replace_the_card_rectangles(self):
        rectangles = []

        self.draw_scene(rectangles)

        drawn_rects = {tuple(args[:4]) for args in rectangles}
        for index in range(len(GUN_SHOP_ORDER)):
            self.assertNotIn(gun_select_card_rect(index), drawn_rects)

    def test_clicking_another_owned_gun_moves_the_selected_slot(self):
        index = GUN_SHOP_ORDER.index("rifle")
        center_x, center_y = self.center_of(index)
        screen_y = SCREEN_HEIGHT - center_y
        self.scene.mouse_move(center_x, screen_y)
        self.scene.mouse_down("left", center_x, screen_y)

        self.selected.draw.reset_mock()
        self.unselected.draw.reset_mock()
        self.draw_scene()

        self.selected.draw.assert_called_once_with(
            center_x, center_y, *GUN_SELECT_SELECTED_SLOT_SIZE
        )


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

        press(self.scene, "space")

        self.assertTrue(self.scene.exit_requested)


class LobbyRecordsImageTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(owned_guns=["pistol"])
        self.table = MagicMock()
        self.book = MagicMock()
        self.scene = LobbyScene(
            Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
            hud_font=MagicMock(),
            state=self.state,
            records_background=self.table,
            records_book_image=self.book,
        )
        self.scene.open_records()

    def exit_button_screen_center(self):
        left, bottom, right, top = records_exit_button_rect()
        return (left + right) / 2, SCREEN_HEIGHT - (bottom + top) / 2

    def test_draws_table_background_and_book_image(self):
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: None)

        self.table.draw.assert_called_once()
        self.book.draw.assert_called_once()

    def test_records_exit_button_is_in_the_bottom_right(self):
        left, bottom, right, top = records_exit_button_rect()

        self.assertGreater(left, SCREEN_WIDTH / 2)
        self.assertLess(top, SCREEN_HEIGHT / 4)
        self.assertEqual(right, SCREEN_WIDTH - 60)
        self.assertGreater(bottom, 0)

    def test_records_exit_button_is_drawn_with_its_label(self):
        rectangles = []
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: rectangles.append(args))

        labels = [entry.args[3] for entry in text_draw.call_args_list]
        drawn_rects = {tuple(args[:4]) for args in rectangles}
        self.assertIn("EXIT", labels)
        self.assertIn(tuple(records_exit_button_rect()), drawn_rects)

    def test_hovering_records_exit_button_sets_hover_state(self):
        screen_x, screen_y = self.exit_button_screen_center()

        self.scene.mouse_move(screen_x, screen_y)

        self.assertTrue(self.scene.records_hover_exit)

    def test_clicking_records_exit_button_returns_to_the_lobby(self):
        screen_x, screen_y = self.exit_button_screen_center()

        self.scene.mouse_down("left", screen_x, screen_y)

        self.assertIsNone(self.scene.panel)
        self.assertFalse(self.scene.records_hover_exit)
        self.assertIsNone(self.scene.pending_action)

    def test_record_text_stays_inside_the_book_paper_area(self):
        self.state.add_record(
            BattleRecord(
                result="victory",
                reached_wave=10,
                elapsed_time=60.0,
            )
        )
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: None)

        book_bottom = (SCREEN_HEIGHT - RECORDS_BOOK_HEIGHT) / 2
        paper_top = SCREEN_HEIGHT - (
            book_bottom + RECORDS_BOOK_PAPER_TOP_IMAGE_Y
        )
        paper_bottom = SCREEN_HEIGHT - (
            book_bottom + RECORDS_BOOK_PAPER_BOTTOM_IMAGE_Y
        )
        calls = text_draw.call_args_list
        ys = [
            entry.args[2]
            for entry in calls
            if entry.args[3] != "EXIT"
        ]
        self.assertTrue(ys)
        for y in ys:
            self.assertGreaterEqual(y, paper_bottom)
            self.assertLessEqual(y, paper_top)

    def test_battle_and_training_records_use_opposite_pages(self):
        self.state.add_record(
            BattleRecord(
                result="defeat",
                reached_wave=7,
                elapsed_time=120.0,
            )
        )
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: None)

        labels = {entry.args[3]: entry.args[1] for entry in text_draw.call_args_list}
        self.assertLess(
            labels["BATTLE RECORDS"], SCREEN_WIDTH / 2
        )
        self.assertGreater(
            labels["TRAINING RECORDS"], SCREEN_WIDTH / 2
        )

    def test_save_recovery_notice_is_drawn(self):
        scene = LobbyScene(
            Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
            hud_font=MagicMock(),
            notice="저장 파일 복구 안내",
        )
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            scene.draw(lambda *args: None)

        texts = [entry.args[3] for entry in text_draw.call_args_list]
        self.assertIn("저장 파일 복구 안내", texts)

    def test_training_record_shows_destroyed_targets(self):
        self.state.add_training_record(TrainingRecord(targets_destroyed=12))
        with patch("lobby_scene.draw_centered_text"), patch(
            "lobby_scene.draw_text_at_center"
        ) as text_draw:
            self.scene.draw(lambda *args: None)

        labels = [entry.args[3] for entry in text_draw.call_args_list]
        self.assertIn("TARGETS 12", labels)
