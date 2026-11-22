"""Integration check of every lobby place and the retry flow."""

import unittest

from battle_scene import BattleResult
from game_config import LOBBY_PLAYER_START_X, LOBBY_PLAYER_START_Y
from lobby_scene import LobbyScene
from main import GameApp
from player import Player


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


def press(app, key):
    app.scene.key_down(key)
    app.scene.key_up(key)


class LobbyPlaceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def test_every_place_can_be_reached_and_used(self):
        press(self.app, "a")
        press(self.app, "a")
        press(self.app, "space")
        self.assertEqual(self.app.scene.pending_action, "enter_shop")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "shop")

        press(self.app, "escape")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "lobby")

        press(self.app, "d")
        press(self.app, "d")
        press(self.app, "d")
        press(self.app, "space")
        self.assertEqual(self.app.scene.pending_action, "enter_training")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "training")

        press(self.app, "escape")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "training")

        self.app.scene.phase = "playing"
        press(self.app, "escape")
        press(self.app, "s")
        press(self.app, "space")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "lobby")

        press(self.app, "a")
        press(self.app, "w")
        press(self.app, "space")
        self.assertEqual(self.app.scene.panel, "gun_select")
        self.assertIsNone(self.app.scene.pending_action)

        press(self.app, "space")
        self.assertTrue(self.app.scene.portal_entry_active)
        self.assertIsNone(self.app.scene.pending_action)

        self.app.scene.update(3.0)
        self.assertEqual(self.app.scene.pending_action, "battle_entry_loading")
        self.app.handle_scene_action()
        self.app.tick_battle_entry_loading(1.0)
        self.assertEqual(self.app.scene_kind, "battle")

    def test_record_place_shows_the_stored_records(self):
        self.app.state.add_record(
            self._make_record("defeat", 2, 40.0)
        )

        press(self.app, "a")
        press(self.app, "space")

        self.assertEqual(self.app.scene.panel, "records")

        press(self.app, "escape")
        self.assertIsNone(self.app.scene.panel)

    def test_retry_after_a_defeat_keeps_the_lobby_usable(self):
        self.app.switch_scene("battle")
        battle = self.app.scene
        battle.result = BattleResult.DEFEAT
        battle.reached_wave = 3
        battle.elapsed_time = 90.0
        battle.coins = 5
        battle.exit_requested = True
        self.app.handle_battle_exit()

        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertAlmostEqual(
            self.app.scene.player.x,
            LOBBY_PLAYER_START_X,
        )
        self.assertAlmostEqual(
            self.app.scene.player.y,
            LOBBY_PLAYER_START_Y,
        )

        press(self.app, "w")
        press(self.app, "space")
        self.assertEqual(self.app.scene.panel, "gun_select")

        press(self.app, "space")
        self.app.scene.update(3.0)
        self.app.handle_scene_action()
        self.app.tick_battle_entry_loading(1.0)

        self.assertEqual(self.app.scene_kind, "battle")
        self.assertEqual(self.app.scene.wave_director.current_wave, 1)

    def test_lobby_keeps_the_coins_earned_in_the_previous_battle(self):
        self.app.switch_scene("battle")
        battle = self.app.scene
        battle.result = BattleResult.VICTORY
        battle.reached_wave = 30
        battle.elapsed_time = 600.0
        battle.clear_time = 580.0
        battle.coins = 25
        battle.exit_requested = True
        self.app.handle_battle_exit()

        self.assertEqual(self.app.state.coins, 25)

    def test_second_retry_after_a_victory_also_works(self):
        for _ in range(2):
            self.app.switch_scene("battle")
            battle = self.app.scene
            battle.result = BattleResult.VICTORY
            battle.reached_wave = 30
            battle.elapsed_time = 600.0
            battle.clear_time = 580.0
            battle.coins = 10
            battle.exit_requested = True
            self.app.handle_battle_exit()

        self.assertEqual(len(self.app.state.records), 2)
        self.assertEqual(self.app.state.coins, 20)

    def test_walking_to_the_stairs_then_pressing_enter_exits_the_game(self):
        press(self.app, "s")

        self.assertEqual(self.app.scene.current_node, "stairs")
        self.assertFalse(self.app.scene.exit_requested)

        press(self.app, "space")

        self.assertTrue(self.app.scene.exit_requested)

        self.app.handle_scene_exit()

        self.assertTrue(self.app.running)
        self.assertTrue(self.app.exit_confirmation_open)
        self.assertFalse(self.app.scene.exit_requested)

    def _make_record(self, result, reached_wave, elapsed_time):
        from battle_record import BattleRecord

        return BattleRecord(
            result=result,
            reached_wave=reached_wave,
            elapsed_time=elapsed_time,
        )


class LobbySceneContractTests(unittest.TestCase):
    def test_lobby_scene_accepts_the_same_calls_as_the_battle_scene(self):
        scene = LobbyScene(Player(0.0, 0.0))

        scene.key_down("w")
        scene.key_up("w")
        scene.mouse_move(100, 200)
        scene.mouse_down("left", 100, 200)
        scene.mouse_up("left")
        scene.update(1.0 / 60)
        scene.draw(lambda *args: None)
        scene.close()

        self.assertFalse(scene.exit_requested)
