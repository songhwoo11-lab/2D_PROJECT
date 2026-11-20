import os
import tempfile
import unittest
from unittest.mock import patch

from battle_scene import BattleResult
from game_config import LOBBY_PLAYER_START_X, LOBBY_PLAYER_START_Y, SCREEN_HEIGHT
from game_state import GameState
from lobby_map import LOBBY_NODE_BY_KEY
from main import GameApp
from save_data import BestLog, SaveData, default_save_data
from save_io import write_save_data
from shop import GUN_SHOP_ORDER
from shop_scene import (
    BUY_ACTION,
    UPGRADE_ACTION,
    button_rect,
    upgrade_confirm_rect,
)
from weapon import PISTOL, RIFLE


def make_app(save_root=None):
    app = GameApp(save_root=save_root)
    app.assets = {
        "lobby_background": None,
        "battle_background": None,
        "player_image": None,
        "gun_image": None,
        "bullet_image": None,
        "arrow_image": None,
        "ammo_image": None,
        "health_image": None,
        "hud_font": None,
        "hit_feedback_font": None,
        "debug_font": None,
        "enemy_images": {},
        "draw_rectangle": None,
        "draw_circle": None,
    }
    return app


def click_shop_button(scene, gun_id, action):
    rect = button_rect(GUN_SHOP_ORDER.index(gun_id), action)
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


def click_upgrade_confirm(scene):
    rect = upgrade_confirm_rect()
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


class SceneSwitchTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def test_app_starts_in_the_lobby(self):
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_shop_return_keeps_the_player_at_the_shop(self):
        self.app.scene.key_down("a")
        self.app.scene.key_up("a")
        self.app.scene.key_down("a")
        self.app.scene.key_up("a")
        self.app.scene.pending_action = "enter_shop"
        self.app.handle_scene_action()
        self.app.scene.pending_action = "return_to_lobby"

        self.app.handle_scene_action()

        node = LOBBY_NODE_BY_KEY["shop"]
        self.assertEqual(self.app.scene.current_node, "shop")
        self.assertAlmostEqual(self.app.scene.player.x, node.zone_x)
        self.assertAlmostEqual(self.app.scene.player.y, node.zone_y)

    def test_training_return_keeps_the_player_at_the_training_ground(self):
        self.app.scene.key_down("d")
        self.app.scene.key_up("d")
        self.app.scene.pending_action = "enter_training"
        self.app.handle_scene_action()
        self.app.scene.pending_action = "return_to_lobby"

        self.app.handle_scene_action()

        node = LOBBY_NODE_BY_KEY["training"]
        self.assertEqual(self.app.scene.current_node, "training")
        self.assertAlmostEqual(self.app.scene.player.x, node.zone_x)
        self.assertAlmostEqual(self.app.scene.player.y, node.zone_y)

    def test_battle_return_keeps_the_player_at_the_portal(self):
        self.app.scene.key_down("w")
        self.app.scene.key_up("w")
        self.app.scene.pending_action = "start_battle"
        self.app.handle_scene_action()
        self.app.scene.result = BattleResult.QUIT

        self.app.handle_scene_exit()

        node = LOBBY_NODE_BY_KEY["portal"]
        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertEqual(self.app.scene.current_node, "portal")
        self.assertAlmostEqual(self.app.scene.player.x, node.zone_x)
        self.assertAlmostEqual(self.app.scene.player.y, node.zone_y)

    def test_lobby_requests_the_shop(self):
        self.app.scene.pending_action = "enter_shop"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "shop")

    def test_shop_returns_to_the_lobby(self):
        self.app.switch_scene("shop")

        self.app.scene.pending_action = "return_to_lobby"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_escape_key_returns_from_shop_to_lobby(self):
        self.app.switch_scene("shop")

        self.app.handle_escape_key()

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_lobby_requests_the_training_ground(self):
        self.app.scene.pending_action = "enter_training"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "training")

    def test_training_ground_returns_to_the_lobby(self):
        self.app.switch_scene("training")

        self.app.scene.pending_action = "return_to_lobby"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_portal_starts_the_battle_scene(self):
        self.app.scene.pending_action = "start_battle"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "battle")

    def test_battle_scene_uses_the_common_pistol_spec(self):
        self.app.switch_scene("battle")

        self.assertIs(self.app.scene.gun.spec, PISTOL)
        self.assertEqual(self.app.scene.gun.gun_id, "pistol")

    def test_battle_scene_uses_the_selected_gun(self):
        self.app.state.owned_guns = ["pistol", "rifle"]
        self.app.state.select_gun("rifle")

        self.app.switch_scene("battle")

        self.assertIs(self.app.scene.gun.spec, RIFLE)

    def test_battle_scene_uses_the_selected_gun_image(self):
        pistol_image = object()
        rifle_image = object()
        self.app.assets["shop_gun_images"] = {
            "pistol": pistol_image,
            "rifle": rifle_image,
            "machine_gun": object(),
        }
        self.app.state.owned_guns = ["pistol", "rifle"]
        self.app.state.select_gun("rifle")

        self.app.switch_scene("battle")

        self.assertIs(self.app.scene.gun_image, rifle_image)

    def test_battle_scene_uses_the_upgraded_gun_stats(self):
        self.app.state.set_upgrade_level("pistol", 1)

        self.app.switch_scene("battle")

        self.assertEqual(self.app.scene.gun.effective_damage, 6)
        self.assertEqual(self.app.scene.gun.magazine_size, 10)

    def test_no_action_keeps_the_current_scene(self):
        self.assertFalse(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_lobby_exit_request_stops_the_game(self):
        self.app.scene.exit_requested = True

        self.app.handle_scene_exit()

        self.assertFalse(self.app.running)
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_escape_stops_the_game_from_the_lobby(self):
        self.app.handle_escape_key()

        self.assertFalse(self.app.running)

    def test_escape_pauses_the_battle_without_stopping_the_game(self):
        self.app.switch_scene("battle")

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertTrue(self.app.scene.paused)

    def test_cursor_visibility_follows_the_active_scene(self):
        with patch("main.pico2d.hide_cursor") as hide, patch(
            "main.pico2d.show_cursor"
        ) as show:
            self.app.scene.shows_system_cursor = False

            self.app.update_cursor_visibility()
            self.app.update_cursor_visibility()

            hide.assert_called_once_with()
            show.assert_not_called()

            self.app.scene.shows_system_cursor = True
            self.app.update_cursor_visibility()
            self.app.update_cursor_visibility()

            show.assert_called_once_with()

    def test_pending_action_is_cleared_after_handling(self):
        self.app.scene.pending_action = "enter_shop"
        self.app.handle_scene_action()

        self.assertIsNone(self.app.scene.pending_action)

    def test_lobby_and_shop_share_the_game_state(self):
        self.app.switch_scene("shop")

        self.assertIs(self.app.scene.state, self.app.state)

    def test_lobby_state_keeps_the_session_progress(self):
        self.app.state.add_record("record")

        self.app.switch_scene("shop")
        self.app.switch_scene("lobby")

        self.assertEqual(len(self.app.state.records), 1)


class BattleReturnTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def _finish_battle(self, result=BattleResult.DEFEAT, coins=12):
        self.app.switch_scene("battle")
        battle = self.app.scene
        battle.result = result
        battle.reached_wave = 5
        battle.elapsed_time = 120.5
        battle.coins = coins
        battle.exit_requested = True
        self.app.handle_battle_exit()

    def test_battle_exit_returns_to_the_lobby(self):
        self._finish_battle()

        self.assertEqual(self.app.scene_kind, "lobby")

    def test_battle_exit_stores_the_earned_coins(self):
        self._finish_battle(coins=12)

        self.assertEqual(self.app.state.coins, 12)

    def test_battle_exit_stores_the_battle_record(self):
        self._finish_battle()

        self.assertEqual(len(self.app.state.records), 1)
        record = self.app.state.records[0]
        self.assertEqual(record.result, BattleResult.DEFEAT.value)
        self.assertEqual(record.reached_wave, 5)
        self.assertAlmostEqual(record.elapsed_time, 120.5)

    def test_victory_record_keeps_the_clear_time(self):
        self.app.switch_scene("battle")
        battle = self.app.scene
        battle.result = BattleResult.VICTORY
        battle.reached_wave = 30
        battle.elapsed_time = 900.0
        battle.clear_time = 880.0
        battle.coins = 40

        self.app.handle_battle_exit()

        record = self.app.state.records[0]
        self.assertAlmostEqual(record.clear_time, 880.0)

    def test_lobby_player_position_is_reset_after_the_battle(self):
        self._finish_battle()
        self.app.scene.player.x = 150.0
        self.app.scene.player.y = 700.0

        self.app.switch_scene("shop")
        self.app.switch_scene("lobby")

        self.assertAlmostEqual(self.app.scene.player.x, LOBBY_PLAYER_START_X)
        self.assertAlmostEqual(self.app.scene.player.y, LOBBY_PLAYER_START_Y)

    def test_reentering_the_battle_starts_from_the_first_wave(self):
        self._finish_battle()
        self.app.switch_scene("battle")

        battle = self.app.scene
        self.assertEqual(battle.wave_director.current_wave, 1)
        self.assertEqual(battle.coins, 0)
        self.assertEqual(battle.pickups, [])
        self.assertEqual(battle.health_pickups, [])

    def test_battle_scene_does_not_leave_objects_in_the_world(self):
        import game_world

        self.app.switch_scene("battle")
        self.app.scene.close()

        self.assertEqual(game_world.world, [[], []])


class ShopEconomyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.state.coins = 1000000

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def _buy_and_upgrade_rifle(self):
        self.app.switch_scene("shop")
        shop = self.app.scene
        click_shop_button(shop, "rifle", BUY_ACTION)
        click_shop_button(shop, "rifle", UPGRADE_ACTION)
        click_upgrade_confirm(shop)
        shop.pending_action = "return_to_lobby"
        self.app.handle_scene_action()

    def test_shop_spending_and_upgrades_follow_the_battle_gun(self):
        self._buy_and_upgrade_rifle()

        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertEqual(self.app.state.coins, 999800)
        self.assertTrue(self.app.state.owns_gun("rifle"))
        self.assertEqual(self.app.state.upgrade_level("rifle"), 1)

        self.app.state.select_gun("rifle")
        self.app.switch_scene("battle")

        gun = self.app.scene.gun
        self.assertEqual(gun.gun_id, "rifle")
        self.assertEqual(gun.effective_damage, 25)
        self.assertEqual(gun.magazine_size, 30)

    def test_battle_rewards_are_added_to_the_post_shop_balance(self):
        self._buy_and_upgrade_rifle()
        balance = self.app.state.coins

        self.app.switch_scene("battle")
        battle = self.app.scene
        battle.coins = 123
        battle.result = BattleResult.VICTORY
        battle.reached_wave = 1
        battle.elapsed_time = 1.0
        battle.clear_time = 1.0
        self.app.handle_battle_exit()

        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertEqual(self.app.state.coins, balance + 123)
        self.assertEqual(self.app.state.records[0].result, "victory")


class SaveStartupIntegrationTests(unittest.TestCase):
    def test_load_progress_applies_saved_state_to_scenes(self):
        data = SaveData(
            acquired_guns=[False, True, False],
            upgrade_levels=[0, 4, 0],
            coins=321,
            best_log=BestLog(reached_wave=15, elapsed_time=250.0),
            recent_logs=[(15, 250.0)],
            training_records=[6],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)
            app = make_app(save_root=temp_dir)
            with patch.dict(os.environ, {}, clear=True):
                app.load_progress()
            app.switch_scene("lobby")

            self.assertEqual(app.state.owned_guns, ["rifle"])
            self.assertEqual(app.state.coins, 321)
            self.assertEqual(app.state.upgrade_level("rifle"), 4)
            self.assertEqual(app.state.selected_gun, "rifle")
            self.assertIs(app.scene.state, app.state)
            self.assertEqual(app.scene.notice, "")
            app.scene.close()

    def test_recovery_notice_is_kept_for_the_lobby(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(default_save_data(), temp_dir)
            from save_paths import gamefile_paths

            gamefile_paths(temp_dir)["coins"].write_text(
                "coins = broken\n", encoding="utf-8"
            )
            app = make_app(save_root=temp_dir)
            with patch.dict(os.environ, {}, clear=True):
                app.load_progress()
            app.switch_scene("lobby")

            self.assertIn("coins.txt", app.save_notice)
            self.assertEqual(app.scene.notice, app.save_notice)
            app.scene.close()
