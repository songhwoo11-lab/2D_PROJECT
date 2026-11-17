"""Integration check of every lobby place and the retry flow."""

import unittest

from battle_scene import BattleResult
from game_config import LOBBY_PLAYER_START_X, LOBBY_PLAYER_START_Y
from lobby_map import LOBBY_STAIRS_EXIT
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


class LobbyPlaceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def _walk_to(self, x, y):
        self.app.scene.player.x = x
        self.app.scene.player.y = y
        self.app.scene.update(1.0 / 60)

    def test_every_place_can_be_reached_and_used(self):
        self._walk_to(330.0, 435.0)
        self.app.scene.key_down("return")
        self.assertEqual(self.app.scene.pending_action, "enter_shop")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "shop")

        self.app.scene.key_down("return")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "lobby")

        self._walk_to(1500.0, 500.0)
        self.app.scene.key_down("return")
        self.assertEqual(self.app.scene.pending_action, "enter_training")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "training")

        self.app.scene.key_down("return")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "lobby")

        self._walk_to(900.0, 620.0)
        self.app.scene.key_down("return")
        self.assertEqual(self.app.scene.pending_action, "start_battle")
        self.app.handle_scene_action()
        self.assertEqual(self.app.scene_kind, "battle")

    def test_record_place_shows_the_stored_records(self):
        self.app.state.add_record(
            self._make_record("defeat", 2, 40.0)
        )

        self._walk_to(600.0, 435.0)
        self.app.scene.key_down("return")

        self.assertEqual(self.app.scene.panel, "records")

        self.app.scene.key_up("return")
        self.app.scene.key_down("return")
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

        self._walk_to(900.0, 620.0)
        self.app.scene.key_down("return")
        self.app.handle_scene_action()

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

    def test_walking_down_the_stairs_exits_the_game(self):
        self._walk_to(LOBBY_STAIRS_EXIT.center_x, 240.0)
        self.app.scene.key_down("s")
        self.app.scene.update(0.25)

        self.assertTrue(self.app.scene.exit_requested)

        self.app.handle_scene_exit()

        self.assertFalse(self.app.running)

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
