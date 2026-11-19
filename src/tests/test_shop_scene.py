import unittest
from unittest import mock

from game_state import GameState
import shop_scene
from shop import GUN_PRICES, gun_price
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

    def test_enter_key_asks_for_the_lobby_return(self):
        self.scene.key_down("space")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_enter_key_is_not_triggered_twice(self):
        self.scene.key_down("space")
        self.scene.pending_action = None

        self.scene.key_down("space")

        self.assertIsNone(self.scene.pending_action)
