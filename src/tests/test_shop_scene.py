import unittest
from unittest import mock

from game_config import HUD_FONT_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH
from game_state import GameState
import shop_scene
from shop import (
    GUN_PRICES,
    MAX_UPGRADE_LEVEL,
    PurchaseResult,
    UpgradeResult,
    gun_price,
    purchase_gun,
)
from shop_scene import (
    BUY_ACTION,
    SHOP_COINS_Y,
    SHOP_EXIT_BUTTON,
    SHOP_LEVEL_Y,
    SHOP_RESULT_Y,
    SHOP_TITLE_Y,
    STATE_ACTION,
    UPGRADE_ACTION,
    UPGRADE_CHANGED_COLOR,
    UPGRADE_MODAL_BUTTON_GAP,
    UPGRADE_MODAL_BUTTON_WIDTH,
    UPGRADE_MODAL_LEFT_RECT,
    UPGRADE_MODAL_RIGHT_RECT,
    button_rect,
    card_rect,
    upgrade_cancel_rect,
    upgrade_confirm_rect,
    upgrade_modal_rect,
    ShopScene,
)
from weapon import weapon_stats_at_level


def draw_and_collect_text(scene):
    with mock.patch.object(shop_scene, "draw_centered_text") as centered:
        with mock.patch.object(shop_scene, "draw_text_at") as positioned:
            scene.draw(lambda *args: None)
    texts = [call.args[2] for call in centered.call_args_list]
    texts.extend(call.args[3] for call in positioned.call_args_list)
    return texts


def click_rect(scene, rect):
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


class ShopLayoutTests(unittest.TestCase):
    def test_cards_are_arranged_horizontally_without_overlap(self):
        rects = [card_rect(index) for index in range(3)]

        for upper, lower in zip(rects, rects[1:]):
            self.assertLessEqual(upper[2], lower[0])

    def test_buttons_are_side_by_side_inside_each_card(self):
        for index in range(3):
            card = card_rect(index)
            buy = button_rect(index, BUY_ACTION)
            upgrade = button_rect(index, UPGRADE_ACTION)

            self.assertLessEqual(buy[2], upgrade[0])
            self.assertGreaterEqual(buy[0], card[0])
            self.assertLessEqual(upgrade[2], card[2])

    def test_state_button_is_below_the_other_buttons_inside_each_card(self):
        for index in range(3):
            card = card_rect(index)
            buy = button_rect(index, BUY_ACTION)
            state = button_rect(index, STATE_ACTION)

            self.assertLess(state[3], buy[1])
            self.assertGreaterEqual(state[0], card[0])
            self.assertLessEqual(state[2], card[2])
            self.assertGreaterEqual(state[1], card[1])
            self.assertLessEqual(state[3], card[3])

    def test_shop_text_rows_do_not_overlap(self):
        rows = [
            SHOP_TITLE_Y,
            SHOP_COINS_Y,
            SHOP_RESULT_Y,
            SHOP_LEVEL_Y,
        ]

        for upper, lower in zip(rows, rows[1:]):
            with self.subTest(upper=upper, lower=lower):
                self.assertGreaterEqual(upper - lower, HUD_FONT_SIZE + 10)

    def test_shop_does_not_show_keyboard_hints(self):
        scene = ShopScene(state=GameState(owned_guns=["pistol"]), hud_font=object())

        texts = draw_and_collect_text(scene)

        for hint in (
            "CLICK BUTTONS OR USE KEYS",
            "W/S GUN  A/D ACTION  SPACE EXECUTE  Q BACK",
        ):
            self.assertNotIn(hint, texts)

    def test_upgrade_modal_buttons_have_equal_width_and_gap(self):
        confirm = upgrade_confirm_rect()
        cancel = upgrade_cancel_rect()

        self.assertEqual(cancel[2] - cancel[0], UPGRADE_MODAL_BUTTON_WIDTH)
        self.assertEqual(confirm[2] - confirm[0], UPGRADE_MODAL_BUTTON_WIDTH)
        self.assertEqual(cancel[0] - confirm[2], UPGRADE_MODAL_BUTTON_GAP)

    def test_exit_button_is_at_the_bottom_right(self):
        left, bottom, right, top = SHOP_EXIT_BUTTON

        self.assertGreater(left, SCREEN_WIDTH / 2)
        self.assertGreater(right, left)
        self.assertLess(bottom, top)
        self.assertLess(top, SCREEN_HEIGHT / 2)


class ShopSceneTests(unittest.TestCase):
    def setUp(self):
        self.scene = ShopScene()

    def tearDown(self):
        self.scene.close()

    def test_shop_scene_starts_without_a_pending_action(self):
        self.assertIsNone(self.scene.pending_action)
        self.assertIsNone(self.scene.state_panel_gun_id)
        self.assertFalse(self.scene.exit_requested)

    def test_update_and_draw_run_without_error(self):
        self.scene.update(1.0 / 60)
        self.scene.draw(lambda *args: None)

    def test_gun_prices_follow_the_prd(self):
        self.assertEqual(
            GUN_PRICES,
            {
                "pistol": 0,
                "rifle": 100000,
                "machine_gun": 1000000,
            },
        )
        self.assertEqual(gun_price("rifle"), 100000)
        with self.assertRaises(KeyError):
            gun_price("unknown")

    def test_shop_draws_card_labels_levels_and_costs(self):
        state = GameState(owned_guns=["pistol"])
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        for expected in (
            "PISTOL",
            "RIFLE",
            "MACHINE GUN",
            "LV 0",
            "COIN 0",
            "COIN 10",
            "COIN 100000",
            "COIN 100",
            "COIN 1000000",
            "COIN 1000",
        ):
            self.assertIn(expected, texts)

    def test_shop_draws_a_state_button_on_every_card(self):
        state = GameState(owned_guns=["pistol"])
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertEqual(texts.count("State"), 3)

    def test_shop_draws_only_english_text(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": 10},
            coins=100000,
        )
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, BUY_ACTION))
        click_rect(scene, button_rect(1, STATE_ACTION))

        texts = draw_and_collect_text(scene)

        for text in texts:
            with self.subTest(text=text):
                self.assertFalse(any("\uac00" <= char <= "\ud7a3" for char in text))

    def test_purchase_button_shows_owned_when_already_owned(self):
        state = GameState(owned_guns=["pistol", "rifle"])
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertEqual(texts.count("OWNED"), 2)
        self.assertIn("BUY", texts)

    def test_upgrade_button_shows_done_at_max_level(self):
        state = GameState(upgrade_levels={"pistol": 10})
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertIn("MAXED", texts)
        self.assertEqual(texts.count("UPGRADE"), 2)
        self.assertIn("LV 10", texts)

    def test_shop_draws_gun_images_above_the_level_labels(self):
        images = {
            "pistol": mock.MagicMock(),
            "rifle": mock.MagicMock(),
            "machine_gun": mock.MagicMock(),
        }
        scene = ShopScene(
            state=GameState(),
            hud_font=object(),
            gun_images=images,
        )

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: None)

        for gun_id, image in images.items():
            self.assertEqual(image.draw.call_count, 1)
            self.assertEqual(
                image.draw.call_args.args,
                (mock.ANY, shop_scene.SHOP_IMAGE_Y) + shop_scene.GUN_IMAGE_SIZES[gun_id],
            )

    def test_shop_draws_the_current_coin_balance(self):
        scene = ShopScene(state=GameState(coins=77), hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertIn("COINS 77", texts)

    def test_shop_draws_the_last_purchase_result(self):
        state = GameState(owned_guns=["pistol"], coins=150000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, BUY_ACTION))

        texts = draw_and_collect_text(scene)

        self.assertTrue(any("PURCHASED RIFLE" in text for text in texts))

    def test_exit_button_click_asks_for_the_lobby_return(self):
        scene = ShopScene(state=GameState(), hud_font=object())

        click_rect(scene, SHOP_EXIT_BUTTON)

        self.assertEqual(scene.pending_action, "return_to_lobby")

    def test_buy_button_click_purchases_that_gun(self):
        state = GameState(owned_guns=["pistol"], coins=150000)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, BUY_ACTION))

        self.assertEqual(scene.gun_index, 1)
        self.assertIn("rifle", state.owned_guns)
        self.assertEqual(state.coins, 50000)

    def test_upgrade_button_click_opens_modal_without_upgrading(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        self.assertEqual(scene.action_index, UPGRADE_ACTION)
        self.assertEqual(scene.upgrade_modal_gun_id, "pistol")
        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertEqual(state.coins, 100)
        self.assertIsNone(scene.last_result)

    def test_upgrade_modal_confirm_applies_the_upgrade(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        click_rect(scene, upgrade_confirm_rect())

        self.assertEqual(state.upgrade_level("pistol"), 1)
        self.assertEqual(state.coins, 90)
        self.assertEqual(scene.last_result.result, UpgradeResult.SUCCESS)
        self.assertIsNone(scene.upgrade_modal_gun_id)

    def test_upgrade_modal_cancel_does_not_upgrade(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        click_rect(scene, upgrade_cancel_rect())

        self.assertIsNone(scene.upgrade_modal_gun_id)
        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertEqual(state.coins, 100)
        self.assertIsNone(scene.last_result)

    def test_clicking_outside_upgrade_modal_closes_it(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        scene.mouse_down("left", 10, SCREEN_HEIGHT - 10)

        self.assertIsNone(scene.upgrade_modal_gun_id)
        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertEqual(state.coins, 100)

    def test_escape_key_cancels_upgrade_modal_instead_of_leaving(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)
        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        scene.key_down("escape")

        self.assertIsNone(scene.upgrade_modal_gun_id)
        self.assertIsNone(scene.pending_action)

    def test_state_button_shows_the_gun_state_without_running_a_function(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, STATE_ACTION))

        self.assertEqual(scene.gun_index, 1)
        self.assertEqual(scene.action_index, STATE_ACTION)
        self.assertEqual(scene.state_panel_gun_id, "rifle")
        self.assertEqual(state.coins, 100000)
        self.assertNotIn("rifle", state.owned_guns)
        self.assertEqual(state.upgrade_level("rifle"), 0)
        self.assertIsNone(scene.last_result)
        self.assertIsNone(scene.pending_action)

        spec = weapon_stats_at_level("rifle", 0)
        texts = draw_and_collect_text(scene)
        for expected in (
            "STATE - RIFLE",
            "NAME RIFLE",
            "LEVEL 0",
            "DAMAGE {}".format(spec.damage),
            "FIRE INTERVAL {:.3f}s".format(spec.fire_interval_seconds),
            "RELOAD TIME {:.1f}s".format(spec.reload_seconds),
            "MAX TEMP {:.1f}".format(spec.temperature_limit),
            "MAGAZINE SIZE {}".format(spec.magazine_size),
            "STARTING AMMO {}".format(spec.starting_ammo),
        ):
            self.assertIn(expected, texts)

        for removed in (
            "GUN ID rifle",
            "PRICE {}".format(gun_price("rifle")),
            "OWNED NO",
        ):
            self.assertNotIn(removed, texts)

    def test_state_panel_uses_the_current_upgrade_level(self):
        state = GameState(
            owned_guns=["pistol", "rifle"],
            upgrade_levels={"rifle": 2},
            coins=100000,
        )
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, STATE_ACTION))

        spec = weapon_stats_at_level("rifle", 2)
        texts = draw_and_collect_text(scene)
        for expected in (
            "LEVEL 2",
            "DAMAGE {}".format(spec.damage),
            "MAGAZINE SIZE {}".format(spec.magazine_size),
            "RELOAD TIME {:.1f}s".format(spec.reload_seconds),
        ):
            self.assertIn(expected, texts)

    def test_state_panel_closes_after_clicking_outside(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, STATE_ACTION))
        self.assertEqual(scene.state_panel_gun_id, "rifle")

        scene.mouse_down("left", 10, SCREEN_HEIGHT - 10)

        self.assertIsNone(scene.state_panel_gun_id)

    def test_click_inside_state_panel_keeps_it_open_and_blocks_buttons(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, STATE_ACTION))

        click_rect(scene, button_rect(1, BUY_ACTION))

        self.assertEqual(scene.state_panel_gun_id, "rifle")
        self.assertEqual(state.coins, 100000)
        self.assertNotIn("rifle", state.owned_guns)
        self.assertIsNone(scene.last_result)

    def test_clicking_another_state_button_switches_the_panel(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, STATE_ACTION))

        click_rect(scene, button_rect(0, STATE_ACTION))

        self.assertEqual(scene.state_panel_gun_id, "pistol")
        self.assertEqual(scene.gun_index, 0)

    def test_state_panel_has_no_unused_space(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, STATE_ACTION))

        rows = scene._state_panel_rows()
        last_y = (
            shop_scene.STATE_PANEL_ROW_TOP
            - (len(rows) - 1) * shop_scene.STATE_PANEL_ROW_GAP
        )
        gap = last_y - shop_scene.STATE_PANEL_BOTTOM

        self.assertEqual(len(rows), 8)
        self.assertGreaterEqual(gap, 0)
        self.assertLessEqual(gap, HUD_FONT_SIZE)

    def test_state_panel_is_drawn_in_the_middle_of_the_shop(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(1, STATE_ACTION))
        rects = []
        expected = shop_scene.state_panel_rect()

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: rects.append(args))

        self.assertIn(expected, [args[:4] for args in rects])

    def test_state_button_hover_target_on_an_unowned_gun(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state)
        rect = button_rect(1, STATE_ACTION)
        center_x = (rect[0] + rect[2]) / 2
        canvas_y = (rect[1] + rect[3]) / 2

        scene.mouse_move(center_x, SCREEN_HEIGHT - canvas_y)

        self.assertEqual(scene.hover_target, ("button", 1, STATE_ACTION))

    def test_state_button_is_not_dimmed_on_an_unowned_gun(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        rects = []

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: rects.append(args))

        button_colors = [
            args[4:7] for args in rects if args[:4] == button_rect(1, STATE_ACTION)
        ]
        self.assertEqual(button_colors, [(62, 74, 96)])

    def test_escape_key_asks_for_the_lobby_return(self):
        self.scene.key_down("escape")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_upgrade_modal_shows_before_after_stats_and_probability(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": 5},
            coins=100000,
        )
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        texts = draw_and_collect_text(scene)

        for expected in (
            "Upgrade?",
            "CURRENT",
            "AFTER",
            "->",
            "UPGRADE CHANCE 50%",
            "SUCCESS 50%  FAIL 44%  DOWN 5%  DESTROY 1%",
            "NAME PISTOL",
            "LEVEL 5",
            "LEVEL 6",
            "UPGRADE",
            "CANCEL",
        ):
            self.assertIn(expected, texts)

    def test_upgrade_modal_draws_both_stat_panels_and_buttons(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))
        rects = []

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: rects.append(args))

        drawn_rects = [args[:4] for args in rects if args[8] is True]
        self.assertIn(upgrade_modal_rect(), drawn_rects)
        self.assertIn(UPGRADE_MODAL_LEFT_RECT, drawn_rects)
        self.assertIn(UPGRADE_MODAL_RIGHT_RECT, drawn_rects)
        self.assertIn(upgrade_confirm_rect(), drawn_rects)
        self.assertIn(upgrade_cancel_rect(), drawn_rects)

    def test_upgrade_modal_marks_changed_after_stats_in_green(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        click_rect(scene, button_rect(0, UPGRADE_ACTION))
        spec = weapon_stats_at_level("pistol", 1)

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at") as positioned:
                scene.draw(lambda *args: None)

        green_texts = [
            call.args[3]
            for call in positioned.call_args_list
            if len(call.args) > 4 and call.args[4] == UPGRADE_CHANGED_COLOR
        ]
        self.assertIn("LEVEL 1", green_texts)
        self.assertIn("DAMAGE {}".format(spec.damage), green_texts)
        self.assertNotIn("LEVEL 0", green_texts)
        self.assertNotIn("NAME PISTOL", green_texts)

    def test_escape_key_is_not_triggered_twice_while_held(self):
        self.scene.key_down("escape")
        self.scene.pending_action = None

        self.scene.key_down("escape")

        self.assertIsNone(self.scene.pending_action)

    def test_escape_key_works_again_after_release(self):
        self.scene.key_down("escape")
        self.scene.pending_action = None
        self.scene.key_up("escape")

        self.scene.key_down("escape")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_removed_keys_do_not_control_the_shop(self):
        state = GameState(owned_guns=["pistol"], coins=150000)
        scene = ShopScene(state=state)
        for key in (
            "w",
            "a",
            "s",
            "d",
            "space",
            "q",
            "return",
            "up",
            "down",
            "left",
            "right",
        ):
            with self.subTest(key=key):
                scene.key_down(key)

                self.assertIsNone(scene.pending_action)
                self.assertEqual(scene.gun_index, 0)
                self.assertEqual(scene.action_index, UPGRADE_ACTION)
                self.assertIsNone(scene.last_result)
                self.assertEqual(state.coins, 150000)


class DisabledShopActionTests(unittest.TestCase):
    def test_owned_gun_starts_on_the_upgrade_action(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)

        self.assertEqual(scene.action_index, UPGRADE_ACTION)

    def test_disabled_purchase_button_is_not_clicked(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)

        click_rect(scene, button_rect(0, BUY_ACTION))

        self.assertEqual(state.coins, 100)
        self.assertIsNone(scene.last_result)
        self.assertNotEqual(scene.action_index, BUY_ACTION)

    def test_disabled_purchase_button_is_not_a_hover_target(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)
        rect = button_rect(0, BUY_ACTION)
        center_x = (rect[0] + rect[2]) / 2
        canvas_y = (rect[1] + rect[3]) / 2

        scene.mouse_move(center_x, SCREEN_HEIGHT - canvas_y)

        self.assertEqual(scene.hover_target, ("card", 0))

    def test_disabled_purchase_button_is_dimmed(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())
        rects = []

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: rects.append(args))

        button_colors = [
            args[4:7] for args in rects if args[:4] == button_rect(0, BUY_ACTION)
        ]
        self.assertEqual(button_colors, [(35, 40, 50)])

    def test_unowned_gun_starts_on_the_purchase_action(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state)

        click_rect(scene, card_rect(1))

        self.assertEqual(scene.gun_index, 1)
        self.assertEqual(scene.action_index, BUY_ACTION)

    def test_disabled_upgrade_button_is_not_clicked_when_not_owned(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, UPGRADE_ACTION))

        self.assertEqual(state.coins, 100000)
        self.assertEqual(state.upgrade_level("rifle"), 0)
        self.assertIsNone(scene.last_result)
        self.assertIsNone(scene.upgrade_modal_gun_id)
        self.assertEqual(scene.action_index, BUY_ACTION)

    def test_disabled_upgrade_button_is_not_a_hover_target_when_not_owned(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state)
        rect = button_rect(1, UPGRADE_ACTION)
        center_x = (rect[0] + rect[2]) / 2
        canvas_y = (rect[1] + rect[3]) / 2

        scene.mouse_move(center_x, SCREEN_HEIGHT - canvas_y)

        self.assertEqual(scene.hover_target, ("card", 1))

    def test_disabled_upgrade_button_is_dimmed_when_not_owned(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())
        rects = []

        with mock.patch.object(shop_scene, "draw_centered_text"):
            with mock.patch.object(shop_scene, "draw_text_at"):
                scene.draw(lambda *args: rects.append(args))

        button_colors = [
            args[4:7] for args in rects if args[:4] == button_rect(1, UPGRADE_ACTION)
        ]
        self.assertEqual(button_colors, [(35, 40, 50)])

    def test_maxed_gun_selects_the_state_action(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": MAX_UPGRADE_LEVEL},
            coins=1000,
        )
        scene = ShopScene(state=state)

        self.assertEqual(scene.action_index, STATE_ACTION)
        self.assertEqual(state.coins, 1000)
        self.assertIsNone(scene.last_result)

    def test_disabled_upgrade_button_is_not_clicked(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": MAX_UPGRADE_LEVEL},
            coins=1000,
        )
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        self.assertEqual(state.coins, 1000)
        self.assertEqual(state.upgrade_level("pistol"), MAX_UPGRADE_LEVEL)
        self.assertIsNone(scene.last_result)
        self.assertIsNone(scene.upgrade_modal_gun_id)
        self.assertEqual(scene.action_index, STATE_ACTION)

    def test_purchase_switches_to_the_upgrade_action(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, BUY_ACTION))

        self.assertIn("rifle", state.owned_guns)
        self.assertEqual(scene.action_index, UPGRADE_ACTION)

    def test_reaching_max_level_selects_the_state_action(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": MAX_UPGRADE_LEVEL - 1},
            coins=100000,
        )
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(0, UPGRADE_ACTION))
        with mock.patch("shop.random.randint", return_value=1):
            click_rect(scene, upgrade_confirm_rect())

        self.assertEqual(state.upgrade_level("pistol"), MAX_UPGRADE_LEVEL)
        self.assertEqual(scene.action_index, STATE_ACTION)
        self.assertIsNone(scene.upgrade_modal_gun_id)


class GunPurchaseTests(unittest.TestCase):
    def test_purchase_deducts_coins_and_adds_ownership(self):
        state = GameState(owned_guns=["pistol"], coins=150000)

        outcome = purchase_gun(state, "rifle")

        self.assertEqual(outcome.result, PurchaseResult.PURCHASED)
        self.assertEqual(outcome.cost, 100000)
        self.assertEqual(state.coins, 50000)
        self.assertIn("rifle", state.owned_guns)

    def test_purchase_is_blocked_when_coins_are_insufficient(self):
        state = GameState(owned_guns=["pistol"], coins=99999)

        outcome = purchase_gun(state, "rifle")

        self.assertEqual(outcome.result, PurchaseResult.INSUFFICIENT_COINS)
        self.assertEqual(outcome.cost, 100000)
        self.assertEqual(state.coins, 99999)
        self.assertNotIn("rifle", state.owned_guns)

    def test_duplicate_purchase_is_blocked(self):
        state = GameState(owned_guns=["pistol", "rifle"], coins=500000)

        outcome = purchase_gun(state, "rifle")

        self.assertEqual(outcome.result, PurchaseResult.ALREADY_OWNED)
        self.assertEqual(outcome.cost, 0)
        self.assertEqual(state.coins, 500000)
        self.assertEqual(state.owned_guns.count("rifle"), 1)

    def test_keys_do_not_buy_but_the_button_still_does(self):
        state = GameState(owned_guns=["pistol"], coins=150000)
        scene = ShopScene(state=state)
        scene.key_down("s")
        scene.key_down("space")

        self.assertEqual(scene.gun_index, 0)
        self.assertNotIn("rifle", state.owned_guns)
        self.assertIsNone(scene.last_result)

        click_rect(scene, button_rect(1, BUY_ACTION))

        self.assertEqual(scene.gun_index, 1)
        self.assertIn("rifle", state.owned_guns)
        self.assertEqual(scene.last_result.result, PurchaseResult.PURCHASED)

    def test_keys_do_not_upgrade_but_the_button_still_does(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)
        scene.key_down("d")
        scene.key_down("space")

        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertIsNone(scene.last_result)

        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        self.assertEqual(scene.action_index, UPGRADE_ACTION)
        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertIsNone(scene.last_result)

        click_rect(scene, upgrade_confirm_rect())

        self.assertEqual(state.upgrade_level("pistol"), 1)
        self.assertEqual(scene.last_result.result, UpgradeResult.SUCCESS)


if __name__ == "__main__":
    unittest.main()
