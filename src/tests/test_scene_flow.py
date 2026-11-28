import os
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from audio import (
    BATTLE_MUSIC_FILE,
    DEFAULT_VOLUME,
    LOBBY_MUSIC_FILE,
    LOBBY_TO_BATTLE_SOUND_FILE,
    MAX_VOLUME,
    MIN_VOLUME,
    SHOP_MUSIC_FILE,
    VOLUME_STEP,
)
from battle_record import BattleRecord
from battle_scene import BattleResult
from game_config import (
    HUD_FONT_SIZE,
    LOBBY_PLAYER_START_X,
    LOBBY_PLAYER_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from game_state import GameState
from lobby_map import LOBBY_NODE_BY_KEY
from main import (
    ASSET_DIRECTORY,
    BATTLE_ENTRY_LOADING_SECONDS,
    EXIT_DIALOG_BUTTON_TEXT_Y,
    EXIT_DIALOG_NO_RECT,
    EXIT_DIALOG_SETTINGS_RECT,
    EXIT_DIALOG_SETTINGS_TEXT,
    EXIT_DIALOG_TEXT_COLOR,
    EXIT_DIALOG_TITLE,
    EXIT_DIALOG_TITLE_Y,
    EXIT_DIALOG_YES_RECT,
    GAME_START_LOADING_SECONDS,
    GameApp,
    LOADING_BACKGROUND_COLOR,
    LOADING_PORTAL_HEIGHT,
    LOADING_PORTAL_WIDTH,
    LOADING_TEXT,
    LOADING_TEXT_COLOR,
    VOLUME_SETTINGS_BACK_RECT,
    VOLUME_SETTINGS_BACK_TEXT,
    VOLUME_SETTINGS_LABEL_COLOR,
    VOLUME_SETTINGS_LABEL_Y,
    VOLUME_SETTINGS_MINUS_RECT,
    VOLUME_SETTINGS_MINUS_TEXT,
    VOLUME_SETTINGS_PLUS_RECT,
    VOLUME_SETTINGS_PLUS_TEXT,
    VOLUME_SETTINGS_SFX_LABEL_Y,
    VOLUME_SETTINGS_SFX_MINUS_RECT,
    VOLUME_SETTINGS_SFX_PLUS_RECT,
    VOLUME_SETTINGS_TITLE,
    VOLUME_SETTINGS_TITLE_Y,
)
from save_data import BestLog, SaveData, default_save_data
from save_io import SaveDataError, load_save_data, write_save_data
from shop import GUN_SHOP_ORDER
from shop_scene import (
    BUY_ACTION,
    UPGRADE_ACTION,
    button_rect as shop_button_rect,
    upgrade_confirm_rect,
)
from title_scene import (
    RESET_BUTTON_INDEX,
    RESET_COMPLETE_SECONDS,
    RESET_DIALOG_NO_RECT,
    RESET_DIALOG_YES_RECT,
    button_rect as title_button_rect,
)
from weapon import PISTOL, RIFLE


def make_app(save_root=None):
    app = GameApp(save_root=save_root)
    app.assets = {
        "lobby_background": None,
        "title_background": None,
        "title_logo": None,
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


class GameAppStartupTests(unittest.TestCase):
    def test_initialize_shows_loading_before_loading_assets_and_creating_the_title(self):
        app = GameApp()
        manager = Mock()
        with patch.object(app, "draw_loading_screen") as draw_loading_screen, patch.object(
            app, "load_progress"
        ) as load_progress, patch.object(app, "load_assets") as load_assets, patch.object(
            app, "switch_scene"
        ) as switch_scene:
            manager.attach_mock(draw_loading_screen, "draw_loading_screen")
            manager.attach_mock(load_progress, "load_progress")
            manager.attach_mock(load_assets, "load_assets")
            manager.attach_mock(switch_scene, "switch_scene")
            app.initialize()

        self.assertEqual(
            manager.mock_calls,
            [
                call.draw_loading_screen(None),
                call.load_progress(),
                call.load_assets(),
                call.switch_scene("title"),
            ],
        )

    def test_draw_loading_screen_draws_loading_text_and_presents_the_canvas(self):
        app = GameApp()
        pico2d_module = Mock()
        with patch("main.draw_centered_text") as draw_text:
            app.draw_loading_screen(pico2d_module)

        pico2d_module.load_font.assert_called_once_with(
            str(ASSET_DIRECTORY / "font" / "MulmaruMono.ttf"),
            HUD_FONT_SIZE,
        )
        pico2d_module.clear_canvas.assert_called_once_with()
        pico2d_module.draw_rectangle.assert_called_once_with(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            *LOADING_BACKGROUND_COLOR,
            True,
        )
        draw_text.assert_called_once_with(
            pico2d_module.load_font.return_value,
            SCREEN_HEIGHT / 2,
            LOADING_TEXT,
            LOADING_TEXT_COLOR,
        )
        pico2d_module.update_canvas.assert_called_once_with()

    def test_draw_loading_screen_draws_the_portal_image_in_the_center(self):
        app = GameApp()
        portal_image = Mock()
        app.assets["portal_image"] = portal_image
        pico2d_module = Mock()

        with patch("main.draw_centered_text"):
            app.draw_loading_screen(pico2d_module, present=False)

        portal_image.draw.assert_called_once_with(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            LOADING_PORTAL_WIDTH,
            LOADING_PORTAL_HEIGHT,
        )
        pico2d_module.update_canvas.assert_not_called()

    def test_run_initializes_the_game_before_entering_the_main_loop(self):
        app = GameApp()
        app.running = False
        with patch("main.pico2d.open_canvas"), patch("main.pico2d.close_canvas"), patch(
            "main.pico2d.show_cursor"
        ), patch.object(app, "initialize") as initialize, patch.object(
            app, "save_progress"
        ):
            app.run()

        initialize.assert_called_once()


def click_shop_button(scene, gun_id, action):
    rect = shop_button_rect(GUN_SHOP_ORDER.index(gun_id), action)
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


def click_upgrade_confirm(scene):
    rect = upgrade_confirm_rect()
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


def click_exit_dialog_button(app, rect):
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    app.handle_exit_confirmation_mouse_down(center_x, SCREEN_HEIGHT - canvas_y)


class SceneSwitchTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def test_app_starts_in_the_lobby(self):
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_switching_to_the_lobby_plays_the_lobby_track(self):
        self.app.audio = Mock()

        self.app.switch_scene("lobby")

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_called_once_with(LOBBY_MUSIC_FILE)

    def test_switching_to_the_shop_plays_the_shop_track(self):
        self.app.audio = Mock()

        self.app.switch_scene("shop")

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_called_once_with(SHOP_MUSIC_FILE)

    def test_switching_to_battle_without_an_entry_animation_starts_music(self):
        self.app.audio = Mock()

        self.app.switch_scene("battle")

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_called_once_with(BATTLE_MUSIC_FILE)

    def test_switching_to_battle_with_an_entry_animation_waits_for_music(self):
        self.app.audio = Mock()

        self.app.switch_scene("battle", portal_transition=True)

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_not_called()

    def test_battle_scene_receives_the_audio_manager(self):
        self.app.switch_scene("battle")

        self.assertIs(self.app.scene.audio, self.app.audio)

    def test_lobby_scene_receives_the_audio_manager(self):
        self.app.switch_scene("lobby")

        self.assertIs(self.app.scene.audio, self.app.audio)

    def test_shop_scene_receives_the_audio_manager(self):
        self.app.switch_scene("shop")

        self.assertIs(self.app.scene.audio, self.app.audio)

    def test_switching_to_a_scene_without_music_only_stops_the_previous_track(self):
        self.app.audio = Mock()

        self.app.switch_scene("training")

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_not_called()

    def test_training_scene_receives_the_audio_manager(self):
        self.app.switch_scene("training")

        self.assertIs(self.app.scene.audio, self.app.audio)
        self.assertFalse(self.app.scene._training_music_started)

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

    def test_escape_before_training_starts_does_not_leave_the_scene(self):
        self.app.switch_scene("training")

        self.app.handle_escape_key()

        self.assertEqual(self.app.scene_kind, "training")
        self.assertFalse(self.app.scene.paused)
        self.assertIsNone(self.app.scene.pending_action)

    def test_escape_during_training_pauses_through_the_app(self):
        self.app.switch_scene("training")
        self.app.scene.phase = "playing"

        self.app.handle_escape_key()

        self.assertEqual(self.app.scene_kind, "training")
        self.assertTrue(self.app.scene.paused)

    def test_pause_menu_lobby_choice_returns_without_a_training_record(self):
        self.app.switch_scene("training")
        self.app.scene.phase = "playing"
        self.app.scene._hits = 3
        self.app.handle_escape_key()
        self.app.scene.key_down("s")
        self.app.scene.key_up("s")
        self.app.scene.key_down("s")
        self.app.scene.key_down("space")

        self.assertTrue(self.app.handle_scene_action())

        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertEqual(self.app.state.training_records, [])

    def test_portal_starts_the_battle_scene(self):
        self.app.scene.pending_action = "start_battle"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "battle")

    def test_escape_is_ignored_during_the_portal_entry_animation(self):
        self.app.scene.portal_entry_active = True

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)

    def test_escape_is_ignored_while_the_battle_loading_screen_is_shown(self):
        self.app.battle_entry_loading_remaining = 1.0

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)

    def test_battle_entry_loading_starts_the_one_second_countdown(self):
        self.app.audio = Mock()
        self.app.scene.pending_action = "battle_entry_loading"

        self.assertTrue(self.app.handle_scene_action())
        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertAlmostEqual(
            self.app.battle_entry_loading_remaining,
            BATTLE_ENTRY_LOADING_SECONDS,
        )
        self.app.audio.play_sound.assert_called_once_with(
            LOBBY_TO_BATTLE_SOUND_FILE
        )

    def test_battle_entry_loading_sound_is_not_replayed_without_a_new_action(self):
        self.app.audio = Mock()
        self.app.scene.pending_action = "battle_entry_loading"
        self.app.handle_scene_action()
        self.app.audio.play_sound.reset_mock()

        self.assertFalse(self.app.handle_scene_action())

        self.app.audio.play_sound.assert_not_called()

    def test_battle_entry_loading_switches_to_battle_after_one_second(self):
        self.app.battle_entry_loading_remaining = BATTLE_ENTRY_LOADING_SECONDS

        self.assertTrue(self.app.tick_battle_entry_loading(0.4))
        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertAlmostEqual(
            self.app.battle_entry_loading_remaining,
            BATTLE_ENTRY_LOADING_SECONDS - 0.4,
        )

        self.assertTrue(self.app.tick_battle_entry_loading(0.6))
        self.assertEqual(self.app.scene_kind, "battle")
        self.assertEqual(self.app.battle_entry_loading_remaining, 0.0)
        self.assertTrue(self.app.scene.portal_transition_active)

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

    def test_lobby_exit_request_opens_the_confirmation_dialog(self):
        self.app.scene.exit_requested = True

        self.app.handle_scene_exit()

        self.assertTrue(self.app.running)
        self.assertTrue(self.app.exit_confirmation_open)
        self.assertFalse(self.app.scene.exit_requested)
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_escape_opens_the_confirmation_dialog_from_the_lobby(self):
        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertTrue(self.app.exit_confirmation_open)

    def test_escape_closes_gun_selection_instead_of_exiting_the_game(self):
        self.app.scene.open_gun_selection()

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertIsNone(self.app.scene.panel)
        self.assertIsNone(self.app.scene.pending_action)

    def test_escape_closes_records_panel_instead_of_exiting_the_game(self):
        self.app.scene.open_records()

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertIsNone(self.app.scene.panel)

    def test_escape_pauses_the_battle_without_stopping_the_game(self):
        self.app.switch_scene("battle")
        self.app.scene.start_countdown_remaining = 0.0

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

    def test_shop_scene_uses_the_shop_ui_images(self):
        background = object()
        selected = object()
        unselected = object()
        self.app.assets["shop_background"] = background
        self.app.assets["shop_selected_slot_image"] = selected
        self.app.assets["shop_unselected_slot_image"] = unselected

        self.app.switch_scene("shop")

        self.assertIs(self.app.scene.background, background)
        self.assertIs(self.app.scene.selected_slot_image, selected)
        self.assertIs(self.app.scene.unselected_slot_image, unselected)

    def test_lobby_scene_uses_the_gun_select_ui_images(self):
        background = object()
        selected = object()
        unselected = object()
        self.app.assets["gun_select_background"] = background
        self.app.assets["shop_selected_slot_image"] = selected
        self.app.assets["shop_unselected_slot_image"] = unselected

        self.app.switch_scene("lobby")

        self.assertIs(self.app.scene.gun_select_background, background)
        self.assertIs(self.app.scene.selected_slot_image, selected)
        self.assertIs(self.app.scene.unselected_slot_image, unselected)

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
        battle.reached_wave = 10
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
            best_log=BestLog(reached_wave=10, elapsed_time=250.0),
            recent_logs=[(10, 250.0)],
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


class SaveExitIntegrationTests(unittest.TestCase):
    def make_loaded_app(self, temp_dir):
        write_save_data(default_save_data(), temp_dir)
        app = make_app(save_root=temp_dir)
        with patch.dict(os.environ, {}, clear=True):
            app.load_progress()
        return app

    def test_battle_exit_updates_coins_and_the_recent_record_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.make_loaded_app(temp_dir)
            app.switch_scene("battle")
            battle = app.scene
            battle.coins = 40
            battle.result = BattleResult.DEFEAT
            battle.reached_wave = 4
            battle.elapsed_time = 33.0

            app.handle_battle_exit()

            saved = load_save_data(temp_dir)
            self.assertEqual(saved.coins, 40)
            self.assertEqual(saved.recent_logs, [(4, 33.0)])
            self.assertEqual(app.state.records[0].result, "defeat")
            app.scene.close()

    def test_quit_to_lobby_does_not_store_a_battle_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.make_loaded_app(temp_dir)
            app.state.add_record(
                BattleRecord("defeat", reached_wave=3, elapsed_time=20.0)
            )
            app.switch_scene("battle")
            battle = app.scene
            battle.coins = 5
            battle.result = BattleResult.QUIT
            battle.reached_wave = 9
            battle.elapsed_time = 60.0

            app.handle_battle_exit()

            self.assertEqual(app.state.coins, 5)
            self.assertEqual(
                [(record.reached_wave, record.result) for record in app.state.records],
                [(3, "defeat")],
            )
            saved = load_save_data(temp_dir)
            self.assertEqual(saved.recent_logs, [(3, 20.0)])
            app.scene.close()

    def test_aborted_battle_without_result_does_not_store_a_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.make_loaded_app(temp_dir)
            app.switch_scene("battle")
            battle = app.scene
            battle.coins = 7
            battle.result = None
            battle.reached_wave = 6
            battle.elapsed_time = 45.0

            app.handle_battle_exit()

            self.assertEqual(app.state.records, [])
            self.assertEqual(load_save_data(temp_dir).recent_logs, [])
            self.assertEqual(app.state.coins, 7)
            app.scene.close()

    def test_save_failure_shows_guidance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.make_loaded_app(temp_dir)

            with patch(
                "main.write_save_data", side_effect=SaveDataError("disk full")
            ):
                self.assertFalse(app.save_progress())

            self.assertIn("disk full", app.save_notice)


class ExitConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("lobby")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def test_no_button_closes_the_dialog_and_keeps_the_game_running(self):
        self.app.open_exit_confirmation()

        click_exit_dialog_button(self.app, EXIT_DIALOG_NO_RECT)

        self.assertTrue(self.app.running)
        self.assertFalse(self.app.exit_confirmation_open)
        self.assertEqual(self.app.scene_kind, "lobby")

    def test_yes_button_closes_the_game(self):
        self.app.open_exit_confirmation()

        click_exit_dialog_button(self.app, EXIT_DIALOG_YES_RECT)

        self.assertFalse(self.app.running)

    def test_escape_closes_the_dialog_without_exiting(self):
        self.app.open_exit_confirmation()

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertFalse(self.app.exit_confirmation_open)

    def test_clicking_outside_the_buttons_keeps_the_dialog_open(self):
        self.app.open_exit_confirmation()

        self.app.handle_exit_confirmation_mouse_down(1, SCREEN_HEIGHT - 1)

        self.assertTrue(self.app.running)
        self.assertTrue(self.app.exit_confirmation_open)

    def test_draw_confirmation_shows_the_title_and_all_three_buttons(self):
        self.app.assets["hud_font"] = object()
        pico2d_module = Mock()
        yes_center_x = (EXIT_DIALOG_YES_RECT[0] + EXIT_DIALOG_YES_RECT[2]) / 2
        no_center_x = (EXIT_DIALOG_NO_RECT[0] + EXIT_DIALOG_NO_RECT[2]) / 2
        settings_center_x = (
            EXIT_DIALOG_SETTINGS_RECT[0] + EXIT_DIALOG_SETTINGS_RECT[2]
        ) / 2
        settings_center_y = (
            EXIT_DIALOG_SETTINGS_RECT[1] + EXIT_DIALOG_SETTINGS_RECT[3]
        ) / 2

        with patch("main.draw_centered_text") as centered_text, patch(
            "main.draw_text_at_center"
        ) as text_at_center:
            self.app.draw_exit_confirmation(pico2d_module)

        centered_text.assert_called_once_with(
            self.app.assets["hud_font"],
            EXIT_DIALOG_TITLE_Y,
            EXIT_DIALOG_TITLE,
            EXIT_DIALOG_TEXT_COLOR,
        )
        self.assertEqual(
            text_at_center.call_args_list,
            [
                call(
                    self.app.assets["hud_font"],
                    yes_center_x,
                    EXIT_DIALOG_BUTTON_TEXT_Y,
                    "YES",
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    no_center_x,
                    EXIT_DIALOG_BUTTON_TEXT_Y,
                    "NO",
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    settings_center_x,
                    settings_center_y,
                    EXIT_DIALOG_SETTINGS_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
            ],
        )
        self.assertEqual(pico2d_module.draw_rectangle.call_count, 5)
        pico2d_module.update_canvas.assert_called_once_with()

    def test_settings_button_opens_the_volume_settings(self):
        self.app.open_exit_confirmation()

        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)

        self.assertTrue(self.app.exit_confirmation_open)
        self.assertTrue(self.app.exit_settings_open)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME)
        self.assertEqual(self.app.audio.sound_volume, DEFAULT_VOLUME)

    def test_music_volume_buttons_adjust_only_music(self):
        self.app.open_exit_confirmation()
        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_PLUS_RECT)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME + VOLUME_STEP)
        self.assertEqual(self.app.audio.sound_volume, DEFAULT_VOLUME)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_MINUS_RECT)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME)

        self.app.set_music_volume(MIN_VOLUME)
        click_exit_dialog_button(self.app, VOLUME_SETTINGS_MINUS_RECT)
        self.assertEqual(self.app.audio.music_volume, MIN_VOLUME)

        self.app.set_music_volume(MAX_VOLUME)
        click_exit_dialog_button(self.app, VOLUME_SETTINGS_PLUS_RECT)
        self.assertEqual(self.app.audio.music_volume, MAX_VOLUME)
        self.assertEqual(self.app.audio.sound_volume, DEFAULT_VOLUME)

    def test_sfx_volume_buttons_adjust_only_effects(self):
        self.app.open_exit_confirmation()
        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_SFX_PLUS_RECT)
        self.assertEqual(self.app.audio.sound_volume, DEFAULT_VOLUME + VOLUME_STEP)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_SFX_MINUS_RECT)
        self.assertEqual(self.app.audio.sound_volume, DEFAULT_VOLUME)

        self.app.set_sound_volume(MIN_VOLUME)
        click_exit_dialog_button(self.app, VOLUME_SETTINGS_SFX_MINUS_RECT)
        self.assertEqual(self.app.audio.sound_volume, MIN_VOLUME)

        self.app.set_sound_volume(MAX_VOLUME)
        click_exit_dialog_button(self.app, VOLUME_SETTINGS_SFX_PLUS_RECT)
        self.assertEqual(self.app.audio.sound_volume, MAX_VOLUME)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME)

    def test_back_button_returns_to_the_exit_dialog(self):
        self.app.open_exit_confirmation()
        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_BACK_RECT)

        self.assertTrue(self.app.exit_confirmation_open)
        self.assertFalse(self.app.exit_settings_open)
        self.assertFalse(self.app.settings_from_pause)

    def test_scene_settings_request_opens_the_panel(self):
        scene = Mock()
        scene.settings_requested = True
        self.app.scene = scene

        self.assertTrue(self.app.consume_settings_request())

        self.assertFalse(scene.settings_requested)
        self.assertTrue(self.app.exit_confirmation_open)
        self.assertTrue(self.app.exit_settings_open)
        self.assertTrue(self.app.settings_from_pause)

    def test_settings_can_be_opened_from_a_paused_scene(self):
        self.app.open_exit_settings(from_pause=True)

        self.assertTrue(self.app.exit_confirmation_open)
        self.assertTrue(self.app.exit_settings_open)
        self.assertTrue(self.app.settings_from_pause)

        self.app.close_exit_settings()

        self.assertFalse(self.app.exit_confirmation_open)
        self.assertFalse(self.app.exit_settings_open)
        self.assertFalse(self.app.settings_from_pause)

    def test_escape_closes_pause_settings_without_opening_the_exit_dialog(self):
        self.app.open_exit_settings(from_pause=True)

        self.app.handle_escape_key()

        self.assertFalse(self.app.exit_confirmation_open)
        self.assertFalse(self.app.exit_settings_open)

    def test_escape_closes_settings_before_closing_the_dialog(self):
        self.app.open_exit_confirmation()
        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)

        self.app.handle_escape_key()
        self.assertTrue(self.app.exit_confirmation_open)
        self.assertFalse(self.app.exit_settings_open)

        self.app.handle_escape_key()
        self.assertFalse(self.app.exit_confirmation_open)

    def test_draw_settings_shows_both_volume_rows_and_controls(self):
        self.app.assets["hud_font"] = object()
        self.app.open_exit_confirmation()
        click_exit_dialog_button(self.app, EXIT_DIALOG_SETTINGS_RECT)
        pico2d_module = Mock()

        def center(rect):
            return (
                (rect[0] + rect[2]) / 2,
                (rect[1] + rect[3]) / 2,
            )

        music_minus_x, music_minus_y = center(VOLUME_SETTINGS_MINUS_RECT)
        music_plus_x, music_plus_y = center(VOLUME_SETTINGS_PLUS_RECT)
        sfx_minus_x, sfx_minus_y = center(VOLUME_SETTINGS_SFX_MINUS_RECT)
        sfx_plus_x, sfx_plus_y = center(VOLUME_SETTINGS_SFX_PLUS_RECT)
        back_x, back_y = center(VOLUME_SETTINGS_BACK_RECT)

        with patch("main.draw_centered_text") as centered_text, patch(
            "main.draw_text_at_center"
        ) as text_at_center:
            self.app.draw_exit_confirmation(pico2d_module)

        self.assertEqual(
            centered_text.call_args_list,
            [
                call(
                    self.app.assets["hud_font"],
                    VOLUME_SETTINGS_TITLE_Y,
                    VOLUME_SETTINGS_TITLE,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    VOLUME_SETTINGS_LABEL_Y,
                    "MUSIC VOLUME: 50 (0-100)",
                    VOLUME_SETTINGS_LABEL_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    VOLUME_SETTINGS_SFX_LABEL_Y,
                    "SFX VOLUME: 50 (0-100)",
                    VOLUME_SETTINGS_LABEL_COLOR,
                ),
            ],
        )
        self.assertEqual(
            text_at_center.call_args_list,
            [
                call(
                    self.app.assets["hud_font"],
                    music_minus_x,
                    music_minus_y,
                    VOLUME_SETTINGS_MINUS_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    music_plus_x,
                    music_plus_y,
                    VOLUME_SETTINGS_PLUS_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    sfx_minus_x,
                    sfx_minus_y,
                    VOLUME_SETTINGS_MINUS_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    sfx_plus_x,
                    sfx_plus_y,
                    VOLUME_SETTINGS_PLUS_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
                call(
                    self.app.assets["hud_font"],
                    back_x,
                    back_y,
                    VOLUME_SETTINGS_BACK_TEXT,
                    EXIT_DIALOG_TEXT_COLOR,
                ),
            ],
        )
        self.assertEqual(pico2d_module.draw_rectangle.call_count, 7)
        pico2d_module.update_canvas.assert_called_once_with()


def click_title_button(app, index):
    rect = title_button_rect(index)
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    app.scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


def click_title_dialog_button(app, rect):
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    app.scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


class TitleFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.app.switch_scene("title")

    def tearDown(self):
        if self.app.scene is not None:
            self.app.scene.close()

    def test_title_scene_uses_the_loaded_background_logo_and_font(self):
        self.assertEqual(self.app.scene_kind, "title")
        self.assertIs(self.app.scene.background, self.app.assets["title_background"])
        self.assertIs(self.app.scene.logo, self.app.assets["title_logo"])
        self.assertIs(self.app.scene.hud_font, self.app.assets["hud_font"])

    def test_title_scene_does_not_play_any_audio(self):
        self.app.audio = Mock()

        self.app.switch_scene("title")

        self.app.audio.stop.assert_called_once_with()
        self.app.audio.play.assert_not_called()
        self.app.audio.play_sound.assert_not_called()

    def test_game_start_shows_loading_before_entering_the_lobby(self):
        click_title_button(self.app, 0)

        self.assertTrue(self.app.handle_scene_action())
        self.assertIsNone(self.app.scene.pending_action)
        self.assertEqual(self.app.scene_kind, "title")
        self.assertAlmostEqual(
            self.app.game_start_loading_remaining,
            GAME_START_LOADING_SECONDS,
        )

        self.assertTrue(self.app.tick_game_start_loading(0.5))
        self.assertEqual(self.app.scene_kind, "title")

        self.assertTrue(self.app.tick_game_start_loading(0.5))
        self.assertEqual(self.app.scene_kind, "lobby")
        self.assertEqual(self.app.game_start_loading_remaining, 0.0)

    def test_escape_is_ignored_while_the_game_start_loading_screen_is_shown(self):
        self.app.game_start_loading_remaining = GAME_START_LOADING_SECONDS

        self.app.handle_escape_key()

        self.assertTrue(self.app.running)
        self.assertEqual(self.app.scene_kind, "title")

    def test_setting_button_opens_sound_settings_and_back_returns_to_the_title(self):
        click_title_button(self.app, 1)

        self.assertTrue(self.app.handle_scene_action())
        self.assertTrue(self.app.exit_settings_open)
        self.assertTrue(self.app.exit_confirmation_open)
        self.assertTrue(self.app.settings_from_pause)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_PLUS_RECT)
        self.assertEqual(self.app.audio.music_volume, DEFAULT_VOLUME + VOLUME_STEP)

        click_exit_dialog_button(self.app, VOLUME_SETTINGS_BACK_RECT)
        self.assertFalse(self.app.exit_settings_open)
        self.assertFalse(self.app.exit_confirmation_open)
        self.assertEqual(self.app.scene_kind, "title")

    def test_exit_game_button_stops_the_game_immediately(self):
        click_title_button(self.app, 3)

        self.assertTrue(self.app.handle_scene_action())

        self.assertFalse(self.app.running)

    def test_reset_game_clears_every_persisted_record(self):
        data = SaveData(
            acquired_guns=[True, True, True],
            upgrade_levels=[2, 4, 6],
            coins=9999,
            best_log=BestLog(reached_wave=10, elapsed_time=1000.0),
            recent_logs=[(10, 1000.0)],
            training_records=[3, 5],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)
            app = make_app(save_root=temp_dir)
            with patch.dict(os.environ, {}, clear=True):
                app.load_progress()
            app.switch_scene("title")

            click_title_button(app, RESET_BUTTON_INDEX)
            self.assertEqual(app.scene.mode, "confirm")

            click_title_dialog_button(app, RESET_DIALOG_YES_RECT)

            self.assertTrue(app.handle_scene_action())
            self.assertEqual(app.scene.mode, "complete")
            self.assertEqual(
                app.scene.reset_complete_remaining,
                RESET_COMPLETE_SECONDS,
            )
            self.assertEqual(load_save_data(temp_dir), default_save_data())
            self.assertEqual(app.state.to_save_data(), default_save_data())
            self.assertEqual(app.state.coins, 0)
            self.assertEqual(app.state.owned_guns, ["pistol"])
            self.assertIsNone(app.state.dev_gun)
            self.assertEqual(app.state.selected_gun, "pistol")
            self.assertIsNone(app.state.best_log)
            self.assertEqual(app.state.records, [])
            self.assertEqual(app.state.training_records, [])
            self.assertEqual(app.save_notice, "")

            app.scene.update(RESET_COMPLETE_SECONDS)
            self.assertEqual(app.scene.mode, "menu")
            self.assertEqual(app.scene_kind, "title")
            app.scene.close()

    def test_reset_no_button_keeps_the_saved_progress(self):
        data = SaveData(
            acquired_guns=[True, True, False],
            upgrade_levels=[0, 4, 0],
            coins=321,
            best_log=BestLog(reached_wave=10, elapsed_time=250.0),
            recent_logs=[(10, 250.0)],
            training_records=[6],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            write_save_data(data, temp_dir)
            app = make_app(save_root=temp_dir)
            with patch.dict(os.environ, {}, clear=True):
                app.load_progress()
            app.switch_scene("title")

            click_title_button(app, RESET_BUTTON_INDEX)
            click_title_dialog_button(app, RESET_DIALOG_NO_RECT)

            self.assertFalse(app.handle_scene_action())
            self.assertEqual(app.scene.mode, "menu")
            self.assertEqual(load_save_data(temp_dir), data)
            self.assertEqual(app.state.coins, 321)
            app.scene.close()
