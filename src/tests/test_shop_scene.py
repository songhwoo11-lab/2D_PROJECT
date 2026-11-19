import unittest
from unittest import mock

from game_state import GameState
import shop_scene
from shop import (
    GUN_PRICES,
    PurchaseResult,
    UpgradeResult,
    gun_price,
    purchase_gun,
)
from shop_scene import ShopScene


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

    def test_shop_draws_each_gun_price_and_ownership(self):
        state = GameState(owned_guns=["pistol", "rifle"])
        scene = ShopScene(state=state, hud_font=object())

        with mock.patch.object(shop_scene, "draw_centered_text") as draw:
            scene.draw(lambda *args: None)

        texts = [call.args[2] for call in draw.call_args_list]
        self.assertIn("PISTOL | PRICE 0 | OWNED", texts)
        self.assertIn("RIFLE | PRICE 100000 | OWNED", texts)
        self.assertIn("MACHINE GUN | PRICE 1000000 | NOT OWNED", texts)

    def test_shop_draws_the_current_coin_balance(self):
        scene = ShopScene(state=GameState(coins=77), hud_font=object())

        with mock.patch.object(shop_scene, "draw_centered_text") as draw:
            scene.draw(lambda *args: None)

        texts = [call.args[2] for call in draw.call_args_list]
        self.assertIn("COINS 77", texts)

    def test_q_key_asks_for_the_lobby_return(self):
        self.scene.key_down("q")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_return_key_asks_for_the_lobby_return(self):
        self.scene.key_down("return")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_return_key_is_not_triggered_twice(self):
        self.scene.key_down("q")
        self.scene.pending_action = None

        self.scene.key_down("q")

        self.assertIsNone(self.scene.pending_action)


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

    def test_space_buys_the_selected_gun(self):
        state = GameState(owned_guns=["pistol"], coins=150000)
        scene = ShopScene(state=state)
        scene.key_down("s")

        scene.key_down("space")

        self.assertEqual(scene.gun_index, 1)
        self.assertIn("rifle", state.owned_guns)
        self.assertEqual(scene.last_result.result, PurchaseResult.PURCHASED)

    def test_d_selects_upgrade_action_and_space_upgrades(self):
        state = GameState(owned_guns=["pistol"], coins=100)
        scene = ShopScene(state=state)
        scene.key_down("d")

        scene.key_down("space")

        self.assertEqual(scene.action_index, 1)
        self.assertEqual(state.upgrade_level("pistol"), 1)
        self.assertEqual(scene.last_result.result, UpgradeResult.SUCCESS)
