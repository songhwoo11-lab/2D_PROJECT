import unittest
from unittest.mock import patch

from battle_scene import BattleResult
from game_config import LOBBY_PLAYER_START_X, LOBBY_PLAYER_START_Y
from game_state import GameState
from lobby_map import LOBBY_NODE_BY_KEY
from main import GameApp
from weapon import PISTOL, RIFLE


def make_app():
    app = GameApp()
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
