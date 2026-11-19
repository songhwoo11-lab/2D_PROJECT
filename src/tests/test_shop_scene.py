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
    NO_ACTION,
    SHOP_COINS_Y,
    SHOP_EXIT_BUTTON,
    SHOP_LEVEL_Y,
    SHOP_RESULT_Y,
    SHOP_TITLE_Y,
    UPGRADE_ACTION,
    button_rect,
    card_rect,
    ShopScene,
)


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

    def test_purchase_button_shows_owned_when_already_owned(self):
        state = GameState(owned_guns=["pistol", "rifle"])
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertEqual(texts.count("소지중"), 2)
        self.assertIn("구매", texts)

    def test_upgrade_button_shows_done_at_max_level(self):
        state = GameState(upgrade_levels={"pistol": 10})
        scene = ShopScene(state=state, hud_font=object())

        texts = draw_and_collect_text(scene)

        self.assertIn("강화완료", texts)
        self.assertEqual(texts.count("강화"), 2)
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

    def test_upgrade_button_click_upgrades_that_gun(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(0, UPGRADE_ACTION))

        self.assertEqual(scene.action_index, UPGRADE_ACTION)
        self.assertEqual(state.upgrade_level("pistol"), 1)
        self.assertEqual(scene.last_result.result, UpgradeResult.SUCCESS)

    def test_escape_key_asks_for_the_lobby_return(self):
        self.scene.key_down("escape")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

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

    def test_maxed_gun_has_no_selectable_action(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": MAX_UPGRADE_LEVEL},
            coins=1000,
        )
        scene = ShopScene(state=state)

        self.assertEqual(scene.action_index, NO_ACTION)
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
        self.assertEqual(scene.action_index, NO_ACTION)

    def test_purchase_switches_to_the_upgrade_action(self):
        state = GameState(owned_guns=["pistol"], coins=100000)
        scene = ShopScene(state=state, hud_font=object())

        click_rect(scene, button_rect(1, BUY_ACTION))

        self.assertIn("rifle", state.owned_guns)
        self.assertEqual(scene.action_index, UPGRADE_ACTION)

    def test_reaching_max_level_clears_the_selected_action(self):
        state = GameState(
            owned_guns=["pistol"],
            upgrade_levels={"pistol": MAX_UPGRADE_LEVEL - 1},
            coins=100000,
        )
        scene = ShopScene(state=state, hud_font=object())

        with mock.patch("shop.random.randint", return_value=1):
            click_rect(scene, button_rect(0, UPGRADE_ACTION))

        self.assertEqual(state.upgrade_level("pistol"), MAX_UPGRADE_LEVEL)
        self.assertEqual(scene.action_index, NO_ACTION)


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
        self.assertEqual(state.upgrade_level("pistol"), 1)
        self.assertEqual(scene.last_result.result, UpgradeResult.SUCCESS)


if __name__ == "__main__":
    unittest.main()
