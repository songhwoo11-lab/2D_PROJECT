"""Pico2D entry point that runs the lobby and the battle scenes."""

from pathlib import Path

import pico2d

from audio import (
    AudioManager,
    LOBBY_TO_BATTLE_SOUND_FILE,
    MUSIC_BY_SCENE,
    MAX_VOLUME,
    MIN_VOLUME,
    VOLUME_STEP,
)
from battle_record import BattleRecord
from battle_scene import (
    DEBUG_FONT_SIZE,
    SHOT_FEEDBACK_FONT_SIZE,
    BattleResult,
    BattleScene,
)
from dev_settings import development_spawn_rate, development_total_waves
from enemy import EnemyType
from game_config import (
    FRAME_TIME,
    HUD_FONT_SIZE,
    LOBBY_PLAYER_START_X,
    LOBBY_PLAYER_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from game_state import GameState
from hud import draw_centered_text, draw_text_at_center
from lobby_map import LOBBY_START_KEY
from lobby_scene import LobbyScene
from player import Player
from save_io import SaveDataError, load_save_data_with_report, write_save_data
from shop_scene import ShopScene
from training_scene import TrainingScene
from weapon import Gun


ASSET_DIRECTORY = Path(__file__).resolve().parent.parent / "image"
LOADING_TEXT = "로딩중..."
LOADING_BACKGROUND_COLOR = (18, 26, 22, 255)
LOADING_TEXT_COLOR = (255, 220, 100)
LOADING_PORTAL_WIDTH = 700
LOADING_PORTAL_HEIGHT = 660
BATTLE_ENTRY_LOADING_SECONDS = 1.0

EXIT_DIALOG_TITLE = "EXIT GAME?"
EXIT_DIALOG_WIDTH = 620
EXIT_DIALOG_HEIGHT = 360
EXIT_DIALOG_LEFT = (SCREEN_WIDTH - EXIT_DIALOG_WIDTH) // 2
EXIT_DIALOG_BOTTOM = (SCREEN_HEIGHT - EXIT_DIALOG_HEIGHT) // 2
EXIT_DIALOG_RIGHT = EXIT_DIALOG_LEFT + EXIT_DIALOG_WIDTH
EXIT_DIALOG_TOP = EXIT_DIALOG_BOTTOM + EXIT_DIALOG_HEIGHT
EXIT_DIALOG_TITLE_Y = EXIT_DIALOG_TOP - 90
EXIT_DIALOG_BUTTON_WIDTH = 180
EXIT_DIALOG_BUTTON_HEIGHT = 80
EXIT_DIALOG_BUTTON_BOTTOM = EXIT_DIALOG_BOTTOM + 70
EXIT_DIALOG_BUTTON_GAP = 60
EXIT_DIALOG_BUTTONS_WIDTH = (
    EXIT_DIALOG_BUTTON_WIDTH * 2 + EXIT_DIALOG_BUTTON_GAP
)
EXIT_DIALOG_YES_RECT = (
    EXIT_DIALOG_LEFT + (EXIT_DIALOG_WIDTH - EXIT_DIALOG_BUTTONS_WIDTH) // 2,
    EXIT_DIALOG_BUTTON_BOTTOM,
    EXIT_DIALOG_LEFT
    + (EXIT_DIALOG_WIDTH - EXIT_DIALOG_BUTTONS_WIDTH) // 2
    + EXIT_DIALOG_BUTTON_WIDTH,
    EXIT_DIALOG_BUTTON_BOTTOM + EXIT_DIALOG_BUTTON_HEIGHT,
)
EXIT_DIALOG_NO_RECT = (
    EXIT_DIALOG_YES_RECT[2] + EXIT_DIALOG_BUTTON_GAP,
    EXIT_DIALOG_BUTTON_BOTTOM,
    EXIT_DIALOG_YES_RECT[2] + EXIT_DIALOG_BUTTON_GAP + EXIT_DIALOG_BUTTON_WIDTH,
    EXIT_DIALOG_BUTTON_BOTTOM + EXIT_DIALOG_BUTTON_HEIGHT,
)
EXIT_DIALOG_BUTTON_TEXT_Y = EXIT_DIALOG_BUTTON_BOTTOM + EXIT_DIALOG_BUTTON_HEIGHT // 2
EXIT_DIALOG_DIM_COLOR = (0, 0, 0, 160)
EXIT_DIALOG_PANEL_COLOR = (30, 42, 38, 255)
EXIT_DIALOG_YES_COLOR = (150, 60, 55, 255)
EXIT_DIALOG_NO_COLOR = (60, 100, 150, 255)
EXIT_DIALOG_TEXT_COLOR = (255, 255, 255)

EXIT_DIALOG_SETTINGS_WIDTH = 220
EXIT_DIALOG_SETTINGS_HEIGHT = 64
EXIT_DIALOG_SETTINGS_BOTTOM = (
    EXIT_DIALOG_BUTTON_BOTTOM + EXIT_DIALOG_BUTTON_HEIGHT + 24
)
EXIT_DIALOG_SETTINGS_RECT = (
    SCREEN_WIDTH / 2 - EXIT_DIALOG_SETTINGS_WIDTH / 2,
    EXIT_DIALOG_SETTINGS_BOTTOM,
    SCREEN_WIDTH / 2 + EXIT_DIALOG_SETTINGS_WIDTH / 2,
    EXIT_DIALOG_SETTINGS_BOTTOM + EXIT_DIALOG_SETTINGS_HEIGHT,
)
EXIT_DIALOG_SETTINGS_COLOR = (60, 120, 90, 255)
EXIT_DIALOG_SETTINGS_TEXT = "SETTINGS"

VOLUME_SETTINGS_TITLE = "SETTINGS"
VOLUME_SETTINGS_TITLE_Y = EXIT_DIALOG_TOP - 50
VOLUME_SETTINGS_LABEL_Y = EXIT_DIALOG_BOTTOM + 240
VOLUME_SETTINGS_SFX_LABEL_Y = EXIT_DIALOG_BOTTOM + 135
VOLUME_SETTINGS_LABEL_COLOR = (255, 220, 100)
VOLUME_SETTINGS_ADJUST_WIDTH = 90
VOLUME_SETTINGS_ADJUST_HEIGHT = 55
VOLUME_SETTINGS_MUSIC_ADJUST_BOTTOM = EXIT_DIALOG_BOTTOM + 165
VOLUME_SETTINGS_SFX_ADJUST_BOTTOM = EXIT_DIALOG_BOTTOM + 60
VOLUME_SETTINGS_MINUS_RECT = (
    SCREEN_WIDTH / 2 - 190,
    VOLUME_SETTINGS_MUSIC_ADJUST_BOTTOM,
    SCREEN_WIDTH / 2 - 190 + VOLUME_SETTINGS_ADJUST_WIDTH,
    VOLUME_SETTINGS_MUSIC_ADJUST_BOTTOM + VOLUME_SETTINGS_ADJUST_HEIGHT,
)
VOLUME_SETTINGS_PLUS_RECT = (
    SCREEN_WIDTH / 2 + 190 - VOLUME_SETTINGS_ADJUST_WIDTH,
    VOLUME_SETTINGS_MUSIC_ADJUST_BOTTOM,
    SCREEN_WIDTH / 2 + 190,
    VOLUME_SETTINGS_MUSIC_ADJUST_BOTTOM + VOLUME_SETTINGS_ADJUST_HEIGHT,
)
VOLUME_SETTINGS_SFX_MINUS_RECT = (
    SCREEN_WIDTH / 2 - 190,
    VOLUME_SETTINGS_SFX_ADJUST_BOTTOM,
    SCREEN_WIDTH / 2 - 190 + VOLUME_SETTINGS_ADJUST_WIDTH,
    VOLUME_SETTINGS_SFX_ADJUST_BOTTOM + VOLUME_SETTINGS_ADJUST_HEIGHT,
)
VOLUME_SETTINGS_SFX_PLUS_RECT = (
    SCREEN_WIDTH / 2 + 190 - VOLUME_SETTINGS_ADJUST_WIDTH,
    VOLUME_SETTINGS_SFX_ADJUST_BOTTOM,
    SCREEN_WIDTH / 2 + 190,
    VOLUME_SETTINGS_SFX_ADJUST_BOTTOM + VOLUME_SETTINGS_ADJUST_HEIGHT,
)
VOLUME_SETTINGS_BACK_RECT = (
    SCREEN_WIDTH / 2 - 90,
    EXIT_DIALOG_BOTTOM + 10,
    SCREEN_WIDTH / 2 + 90,
    EXIT_DIALOG_BOTTOM + 50,
)
VOLUME_SETTINGS_ADJUST_COLOR = (90, 90, 110, 255)
VOLUME_SETTINGS_BACK_COLOR = EXIT_DIALOG_NO_COLOR
VOLUME_SETTINGS_MINUS_TEXT = "-"
VOLUME_SETTINGS_PLUS_TEXT = "+"
VOLUME_SETTINGS_BACK_TEXT = "BACK"


def point_in_rect(rect, x, y):
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def rect_center(rect):
    return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2


class GameApp:
    """Loads the shared assets and keeps the currently active scene."""

    def __init__(self, save_root=None):
        self.assets = {}
        self.state = GameState()
        self.save_root = save_root
        self.save_notice = ""
        self.scene = None
        self.scene_kind = None
        self.lobby_node_key = LOBBY_START_KEY
        self.cursor_hidden = False
        self.running = True
        self.battle_entry_loading_remaining = 0.0
        self.loading_font = None
        self.exit_confirmation_open = False
        self.exit_settings_open = False
        self.settings_from_pause = False
        self.audio = AudioManager()

    def draw_loading_screen(self, pico2d_module=None, present=True):
        pico2d_module = pico2d_module or pico2d
        if self.loading_font is None:
            self.loading_font = pico2d_module.load_font(
                str(ASSET_DIRECTORY / "font" / "MulmaruMono.ttf"),
                HUD_FONT_SIZE,
            )
        font = self.loading_font
        pico2d_module.clear_canvas()
        pico2d_module.draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            *LOADING_BACKGROUND_COLOR,
            True,
        )
        portal_image = self.assets.get("portal_image")
        if portal_image is not None:
            portal_image.draw(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                LOADING_PORTAL_WIDTH,
                LOADING_PORTAL_HEIGHT,
            )
        draw_centered_text(
            font,
            SCREEN_HEIGHT / 2,
            LOADING_TEXT,
            LOADING_TEXT_COLOR,
        )
        if present:
            pico2d_module.update_canvas()

    def draw_exit_confirmation(self, pico2d_module=None, present=True):
        if self.exit_settings_open:
            self.draw_volume_settings(pico2d_module, present)
            return
        pico2d_module = pico2d_module or pico2d
        pico2d_module.draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            *EXIT_DIALOG_DIM_COLOR,
            True,
        )
        pico2d_module.draw_rectangle(
            EXIT_DIALOG_LEFT,
            EXIT_DIALOG_BOTTOM,
            EXIT_DIALOG_RIGHT,
            EXIT_DIALOG_TOP,
            *EXIT_DIALOG_PANEL_COLOR,
            True,
        )
        pico2d_module.draw_rectangle(
            *EXIT_DIALOG_YES_RECT,
            *EXIT_DIALOG_YES_COLOR,
            True,
        )
        pico2d_module.draw_rectangle(
            *EXIT_DIALOG_NO_RECT,
            *EXIT_DIALOG_NO_COLOR,
            True,
        )
        pico2d_module.draw_rectangle(
            *EXIT_DIALOG_SETTINGS_RECT,
            *EXIT_DIALOG_SETTINGS_COLOR,
            True,
        )
        font = self.assets.get("hud_font")
        if font is not None:
            draw_centered_text(
                font,
                EXIT_DIALOG_TITLE_Y,
                EXIT_DIALOG_TITLE,
                EXIT_DIALOG_TEXT_COLOR,
            )
            draw_text_at_center(
                font,
                (EXIT_DIALOG_YES_RECT[0] + EXIT_DIALOG_YES_RECT[2]) / 2,
                EXIT_DIALOG_BUTTON_TEXT_Y,
                "YES",
                EXIT_DIALOG_TEXT_COLOR,
            )
            draw_text_at_center(
                font,
                (EXIT_DIALOG_NO_RECT[0] + EXIT_DIALOG_NO_RECT[2]) / 2,
                EXIT_DIALOG_BUTTON_TEXT_Y,
                "NO",
                EXIT_DIALOG_TEXT_COLOR,
            )
            settings_x, settings_y = rect_center(EXIT_DIALOG_SETTINGS_RECT)
            draw_text_at_center(
                font,
                settings_x,
                settings_y,
                EXIT_DIALOG_SETTINGS_TEXT,
                EXIT_DIALOG_TEXT_COLOR,
            )
        if present:
            pico2d_module.update_canvas()

    def draw_volume_settings(self, pico2d_module=None, present=True):
        pico2d_module = pico2d_module or pico2d
        pico2d_module.draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            *EXIT_DIALOG_DIM_COLOR,
            True,
        )
        pico2d_module.draw_rectangle(
            EXIT_DIALOG_LEFT,
            EXIT_DIALOG_BOTTOM,
            EXIT_DIALOG_RIGHT,
            EXIT_DIALOG_TOP,
            *EXIT_DIALOG_PANEL_COLOR,
            True,
        )
        for rect in (
            VOLUME_SETTINGS_MINUS_RECT,
            VOLUME_SETTINGS_PLUS_RECT,
            VOLUME_SETTINGS_SFX_MINUS_RECT,
            VOLUME_SETTINGS_SFX_PLUS_RECT,
        ):
            pico2d_module.draw_rectangle(
                *rect,
                *VOLUME_SETTINGS_ADJUST_COLOR,
                True,
            )
        pico2d_module.draw_rectangle(
            *VOLUME_SETTINGS_BACK_RECT,
            *VOLUME_SETTINGS_BACK_COLOR,
            True,
        )
        font = self.assets.get("hud_font")
        if font is not None:
            draw_centered_text(
                font,
                VOLUME_SETTINGS_TITLE_Y,
                VOLUME_SETTINGS_TITLE,
                EXIT_DIALOG_TEXT_COLOR,
            )
            draw_centered_text(
                font,
                VOLUME_SETTINGS_LABEL_Y,
                "MUSIC VOLUME: {} ({}-{})".format(
                    self.audio.music_volume, MIN_VOLUME, MAX_VOLUME
                ),
                VOLUME_SETTINGS_LABEL_COLOR,
            )
            draw_centered_text(
                font,
                VOLUME_SETTINGS_SFX_LABEL_Y,
                "SFX VOLUME: {} ({}-{})".format(
                    self.audio.sound_volume, MIN_VOLUME, MAX_VOLUME
                ),
                VOLUME_SETTINGS_LABEL_COLOR,
            )
            adjust_rects = (
                (VOLUME_SETTINGS_MINUS_RECT, VOLUME_SETTINGS_MINUS_TEXT),
                (VOLUME_SETTINGS_PLUS_RECT, VOLUME_SETTINGS_PLUS_TEXT),
                (VOLUME_SETTINGS_SFX_MINUS_RECT, VOLUME_SETTINGS_MINUS_TEXT),
                (VOLUME_SETTINGS_SFX_PLUS_RECT, VOLUME_SETTINGS_PLUS_TEXT),
                (VOLUME_SETTINGS_BACK_RECT, VOLUME_SETTINGS_BACK_TEXT),
            )
            for rect, text in adjust_rects:
                x, y = rect_center(rect)
                draw_text_at_center(font, x, y, text, EXIT_DIALOG_TEXT_COLOR)
        if present:
            pico2d_module.update_canvas()

    def initialize(self, pico2d_module=None):
        self.draw_loading_screen(pico2d_module)
        self.load_progress()
        self.load_assets()
        self.switch_scene("lobby")

    def load_progress(self):
        """Load saved progress into the state and keep recovery guidance."""
        result = load_save_data_with_report(self.save_root)
        self.state = GameState.from_save_data(result.data)
        self.save_notice = result.guidance_text() if result.recovered else ""
        if self.save_notice:
            print("저장 데이터 안내: " + self.save_notice)
        return result

    def save_progress(self):
        """Persist the current state, reporting write failures clearly."""
        try:
            write_save_data(self.state.to_save_data(), self.save_root)
            return True
        except SaveDataError as error:
            message = "저장 파일을 갱신할 수 없습니다: {}".format(error)
            self.save_notice = message
            print("저장 데이터 안내: " + message)
            return False

    def load_assets(self):
        import pico2d

        directory = ASSET_DIRECTORY
        self.assets["draw_rectangle"] = pico2d.draw_rectangle
        self.assets["draw_circle"] = pico2d.draw_circle
        self.assets["battle_background"] = pico2d.load_image(
            str(directory / "in_game.png")
        )
        self.assets["lobby_background"] = pico2d.load_image(
            str(directory / "game_lobby.png")
        )
        self.assets["player_image"] = pico2d.load_image(str(directory / "boy.png"))
        self.assets["portal_image"] = pico2d.load_image(
            str(directory / "portal_image.png")
        )
        self.assets["gun_image"] = pico2d.load_image(str(directory / "gun.png"))
        self.assets["shop_gun_images"] = {
            "pistol": self.assets["gun_image"],
            "rifle": pico2d.load_image(str(directory / "rifle.png")),
            "machine_gun": pico2d.load_image(str(directory / "machineGun.png")),
        }
        self.assets["shop_background"] = pico2d.load_image(
            str(directory / "shop.png")
        )
        self.assets["shop_selected_slot_image"] = pico2d.load_image(
            str(directory / "selected_gun.png")
        )
        self.assets["shop_unselected_slot_image"] = pico2d.load_image(
            str(directory / "unselected_gun.png")
        )
        self.assets["bullet_image"] = pico2d.load_image(str(directory / "bullet.png"))
        self.assets["arrow_image"] = pico2d.load_image(str(directory / "arrow.png"))
        self.assets["ammo_image"] = pico2d.load_image(str(directory / "ammo.png"))
        self.assets["health_image"] = pico2d.load_image(
            str(directory / "health potion.png")
        )
        self.assets["cooling_image"] = pico2d.load_image(
            str(directory / "ice potion.png")
        )
        self.assets["training_target_image"] = pico2d.load_image(
            str(directory / "Training_Target.png")
        )
        self.assets["training_background"] = pico2d.load_image(
            str(directory / "game_training.png")
        )
        self.assets["records_background"] = pico2d.load_image(
            str(directory / "table.png")
        )
        self.assets["records_book_image"] = pico2d.load_image(
            str(directory / "book.png")
        )
        self.assets["gun_select_background"] = pico2d.load_image(
            str(directory / "potal.png")
        )
        self.assets["hud_font"] = pico2d.load_font(
            str(directory / "font" / "MulmaruMono.ttf"),
            HUD_FONT_SIZE,
        )
        self.assets["hit_feedback_font"] = pico2d.load_font(
            str(directory / "font" / "BMEuljiro10yearslater.ttf"),
            SHOT_FEEDBACK_FONT_SIZE,
        )
        self.assets["debug_font"] = pico2d.load_font(
            str(directory / "font" / "MulmaruMono.ttf"),
            DEBUG_FONT_SIZE,
        )
        self.assets["enemy_images"] = {
            EnemyType.BASIC: pico2d.load_image(str(directory / "common_skel.png")),
            EnemyType.EXPLOSIVE: pico2d.load_image(
                str(directory / "boom skel.png")
            ),
            EnemyType.TANKER: pico2d.load_image(str(directory / "tanker_skel.png")),
            EnemyType.ASSASSIN: pico2d.load_image(
                str(directory / "assassin_skel.png")
            ),
            EnemyType.ARCHER: pico2d.load_image(str(directory / "bow_skel.png")),
        }
        self.audio.set_loader(pico2d.load_music)
        self.audio.set_sound_loader(pico2d.load_wav)

    def create_lobby_scene(self):
        player = Player(
            LOBBY_PLAYER_START_X,
            LOBBY_PLAYER_START_Y,
            image=self.assets["player_image"],
        )
        return LobbyScene(
            player,
            self.assets["lobby_background"],
            hud_font=self.assets["hud_font"],
            state=self.state,
            node_key=self.lobby_node_key,
            gun_images=self.assets.get("shop_gun_images"),
            gun_select_background=self.assets.get("gun_select_background"),
            selected_slot_image=self.assets.get("shop_selected_slot_image"),
            unselected_slot_image=self.assets.get("shop_unselected_slot_image"),
            records_background=self.assets.get("records_background"),
            records_book_image=self.assets.get("records_book_image"),
            notice=self.save_notice,
            audio=self.audio,
        )

    def create_battle_scene(self, portal_transition=False):
        player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=self.assets["player_image"],
        )
        gun_images = self.assets.get("shop_gun_images", {})
        gun_image = gun_images.get(
            self.state.selected_gun,
            self.assets["gun_image"],
        )
        return BattleScene(
            player,
            Gun.from_gun_id(
                self.state.selected_gun,
                self.state.upgrade_level(self.state.selected_gun),
            ),
            self.assets["battle_background"],
            gun_image=gun_image,
            gun_images=gun_images,
            bullet_image=self.assets["bullet_image"],
            hud_font=self.assets["hud_font"],
            hit_feedback_font=self.assets["hit_feedback_font"],
            debug_font=self.assets["debug_font"],
            enemy_images=self.assets["enemy_images"],
            enemy_draw_rectangle=self.assets["draw_rectangle"],
            enemy_draw_circle=self.assets["draw_circle"],
            arrow_image=self.assets["arrow_image"],
            ammo_image=self.assets["ammo_image"],
            health_image=self.assets["health_image"],
            cooling_image=self.assets.get("cooling_image"),
            portal_image=self.assets.get("portal_image"),
            portal_transition=portal_transition,
            total_waves=development_total_waves(),
            wave_spawn_rate=development_spawn_rate(),
            audio=self.audio,
        )

    def switch_scene(self, kind, portal_transition=False):
        if self.scene_kind == "lobby" and self.scene is not None:
            self.lobby_node_key = getattr(
                self.scene, "current_node", LOBBY_START_KEY
            )
        if self.scene is not None:
            self.scene.close()
        self.audio.stop()
        if kind == "lobby":
            self.scene = self.create_lobby_scene()
        elif kind == "battle":
            self.scene = self.create_battle_scene(
                portal_transition=portal_transition
            )
        elif kind == "shop":
            self.scene = self.create_shop_scene()
        elif kind == "training":
            self.scene = self.create_training_scene()
        else:
            raise ValueError("unknown scene: {}".format(kind))
        self.scene_kind = kind
        music_file = MUSIC_BY_SCENE.get(kind)
        if music_file is not None:
            self.audio.play(music_file)

    def create_shop_scene(self):
        return ShopScene(
            state=self.state,
            hud_font=self.assets["hud_font"],
            gun_images=self.assets.get("shop_gun_images"),
            background=self.assets.get("shop_background"),
            selected_slot_image=self.assets.get("shop_selected_slot_image"),
            unselected_slot_image=self.assets.get("shop_unselected_slot_image"),
            audio=self.audio,
        )

    def create_training_scene(self):
        player = Player(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            image=self.assets["player_image"],
        )
        return TrainingScene(
            player=player,
            gun=Gun.from_gun_id(
                self.state.selected_gun,
                self.state.upgrade_level(self.state.selected_gun),
            ),
            background=self.assets.get("training_background"),
            hud_font=self.assets["hud_font"],
            state=self.state,
            target_image=self.assets.get("training_target_image"),
            audio=self.audio,
        )

    def handle_scene_action(self):
        """Move to the next scene when the active scene asks for it."""
        action = getattr(self.scene, "pending_action", None)
        if action is None:
            return False
        self.scene.pending_action = None
        if action == "enter_shop":
            self.switch_scene("shop")
            return True
        if action == "enter_training":
            self.switch_scene("training")
            return True
        if action == "start_battle":
            self.switch_scene("battle")
            return True
        if action == "battle_entry_loading":
            self.battle_entry_loading_remaining = BATTLE_ENTRY_LOADING_SECONDS
            self.audio.play_sound(LOBBY_TO_BATTLE_SOUND_FILE)
            return True
        if action == "return_to_lobby":
            self.switch_scene("lobby")
            return True
        raise ValueError("unknown scene action: {}".format(action))

    def tick_battle_entry_loading(self, delta_time):
        if self.battle_entry_loading_remaining <= 0.0:
            return False
        self.battle_entry_loading_remaining = max(
            0.0, self.battle_entry_loading_remaining - delta_time
        )
        if self.battle_entry_loading_remaining == 0.0:
            self.switch_scene("battle", portal_transition=True)
        return True

    def handle_scene_exit(self):
        """Handle the active scene's request to leave the game."""
        if self.scene_kind == "battle":
            self.handle_battle_exit()
            return
        self.open_exit_confirmation()

    def set_music_volume(self, volume):
        return self.audio.set_music_volume(volume)

    def set_sound_volume(self, volume):
        return self.audio.set_sound_volume(volume)

    def change_music_volume(self, amount):
        return self.audio.change_music_volume(amount)

    def change_sound_volume(self, amount):
        return self.audio.change_sound_volume(amount)

    def open_exit_confirmation(self):
        if self.exit_confirmation_open:
            return
        self.exit_confirmation_open = True
        self.exit_settings_open = False
        self.settings_from_pause = False
        if self.scene is not None and getattr(self.scene, "exit_requested", False):
            self.scene.exit_requested = False

    def close_exit_confirmation(self):
        self.exit_confirmation_open = False
        self.exit_settings_open = False
        self.settings_from_pause = False

    def open_exit_settings(self, from_pause=False):
        self.settings_from_pause = from_pause
        self.exit_settings_open = True
        if from_pause:
            self.exit_confirmation_open = True

    def close_exit_settings(self):
        self.exit_settings_open = False
        if self.settings_from_pause:
            self.exit_confirmation_open = False
            self.settings_from_pause = False

    def consume_settings_request(self):
        if self.exit_confirmation_open:
            return False
        if not getattr(self.scene, "settings_requested", False):
            return False
        self.scene.settings_requested = False
        self.open_exit_settings(from_pause=True)
        return True

    def handle_exit_confirmation_mouse_down(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        if self.exit_settings_open:
            if point_in_rect(VOLUME_SETTINGS_MINUS_RECT, screen_x, canvas_y):
                self.change_music_volume(-VOLUME_STEP)
            elif point_in_rect(VOLUME_SETTINGS_PLUS_RECT, screen_x, canvas_y):
                self.change_music_volume(VOLUME_STEP)
            elif point_in_rect(VOLUME_SETTINGS_SFX_MINUS_RECT, screen_x, canvas_y):
                self.change_sound_volume(-VOLUME_STEP)
            elif point_in_rect(VOLUME_SETTINGS_SFX_PLUS_RECT, screen_x, canvas_y):
                self.change_sound_volume(VOLUME_STEP)
            elif point_in_rect(VOLUME_SETTINGS_BACK_RECT, screen_x, canvas_y):
                self.close_exit_settings()
            return
        if point_in_rect(EXIT_DIALOG_SETTINGS_RECT, screen_x, canvas_y):
            self.open_exit_settings()
            return
        if point_in_rect(EXIT_DIALOG_YES_RECT, screen_x, canvas_y):
            self.running = False
            return
        if point_in_rect(EXIT_DIALOG_NO_RECT, screen_x, canvas_y):
            self.close_exit_confirmation()

    def handle_escape_key(self):
        if self.exit_settings_open:
            self.close_exit_settings()
            return
        if self.exit_confirmation_open:
            self.close_exit_confirmation()
            return
        if self.battle_entry_loading_remaining > 0.0:
            return
        if self.scene_kind == "lobby":
            if getattr(self.scene, "portal_entry_active", False):
                return
            if getattr(self.scene, "panel", None) in ("gun_select", "records"):
                self.scene.key_down("escape")
                return
            self.open_exit_confirmation()
            return
        self.scene.key_down("escape")

    def update_cursor_visibility(self):
        if self.exit_confirmation_open:
            should_hide = False
        else:
            should_hide = not bool(getattr(self.scene, "shows_system_cursor", True))
        if should_hide == self.cursor_hidden:
            return
        if should_hide:
            pico2d.hide_cursor()
        else:
            pico2d.show_cursor()
        self.cursor_hidden = should_hide

    def handle_battle_exit(self):
        """Store a finished battle result, unless the battle was abandoned."""
        battle = self.scene
        self.state.coins += battle.coins
        abandoned = battle.result is None or battle.result is BattleResult.QUIT
        if not abandoned:
            self.state.add_record(
                BattleRecord(
                    result=battle.result.value,
                    reached_wave=battle.reached_wave,
                    elapsed_time=battle.elapsed_time,
                    clear_time=battle.clear_time,
                )
            )
        self.save_progress()
        self.switch_scene("lobby")

    def run(self):
        import pico2d

        pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
        try:
            self.initialize(pico2d)
            key_map = {
                pico2d.SDLK_F1: "f1",
                pico2d.SDLK_w: "w",
                pico2d.SDLK_a: "a",
                pico2d.SDLK_s: "s",
                pico2d.SDLK_d: "d",
                pico2d.SDLK_e: "e",
                pico2d.SDLK_r: "r",
                pico2d.SDLK_SPACE: "space",
                pico2d.SDLK_q: "q",
                pico2d.SDLK_UP: "up",
                pico2d.SDLK_DOWN: "down",
                pico2d.SDLK_LEFT: "left",
                pico2d.SDLK_RIGHT: "right",
                pico2d.SDLK_RETURN: "return",
                pico2d.SDLK_ESCAPE: "escape",
            }

            last_time = pico2d.get_time()
            while self.running:
                frame_start = pico2d.get_time()
                delta_time = min(max(frame_start - last_time, 0.0), 0.1)
                for event in pico2d.get_events():
                    if event.type == pico2d.SDL_QUIT:
                        self.open_exit_confirmation()
                    elif event.type == pico2d.SDL_KEYDOWN:
                        if event.key == pico2d.SDLK_ESCAPE:
                            self.handle_escape_key()
                        elif (
                            self.exit_settings_open
                            and event.key == pico2d.SDLK_UP
                        ):
                            self.change_music_volume(VOLUME_STEP)
                        elif (
                            self.exit_settings_open
                            and event.key == pico2d.SDLK_DOWN
                        ):
                            self.change_music_volume(-VOLUME_STEP)
                        elif (
                            self.exit_settings_open
                            and event.key == pico2d.SDLK_RIGHT
                        ):
                            self.change_sound_volume(VOLUME_STEP)
                        elif (
                            self.exit_settings_open
                            and event.key == pico2d.SDLK_LEFT
                        ):
                            self.change_sound_volume(-VOLUME_STEP)
                        elif event.key in key_map and not self.exit_confirmation_open:
                            self.scene.key_down(key_map[event.key])
                    elif event.type == pico2d.SDL_KEYUP:
                        if event.key in key_map:
                            self.scene.key_up(key_map[event.key])
                    elif event.type == pico2d.SDL_MOUSEMOTION:
                        if not self.exit_confirmation_open:
                            self.scene.mouse_move(event.x, event.y)
                    elif event.type == pico2d.SDL_MOUSEBUTTONDOWN:
                        if event.button == pico2d.SDL_BUTTON_LEFT:
                            if self.exit_confirmation_open:
                                self.handle_exit_confirmation_mouse_down(
                                    event.x, event.y
                                )
                            else:
                                self.scene.mouse_down("left", event.x, event.y)
                    elif event.type == pico2d.SDL_MOUSEBUTTONUP:
                        if (
                            event.button == pico2d.SDL_BUTTON_LEFT
                            and not self.exit_confirmation_open
                        ):
                            self.scene.mouse_up("left")

                showing_battle_loading = False
                if not self.exit_confirmation_open:
                    self.scene.update(delta_time)
                    if not self.consume_settings_request():
                        self.handle_scene_action()
                        showing_battle_loading = self.tick_battle_entry_loading(
                            delta_time
                        )
                pico2d.clear_canvas()
                if showing_battle_loading:
                    self.draw_loading_screen(pico2d, present=False)
                else:
                    self.scene.draw(pico2d.draw_rectangle)
                if self.exit_confirmation_open:
                    self.draw_exit_confirmation(pico2d, present=False)
                self.update_cursor_visibility()
                pico2d.update_canvas()
                if self.scene.exit_requested:
                    self.handle_scene_exit()
                frame_duration = pico2d.get_time() - frame_start
                pico2d.delay(max(0.0, FRAME_TIME - frame_duration))
                last_time = frame_start
        finally:
            self.save_progress()
            if self.scene is not None:
                self.scene.close()
            if self.cursor_hidden:
                pico2d.show_cursor()
                self.cursor_hidden = False
            pico2d.close_canvas()


def main():
    try:
        import pico2d
    except ModuleNotFoundError as error:
        if error.name != "pico2d":
            raise
        raise RuntimeError(
            "Pico2D is required to run the game. Install Pico2D in this Python environment."
        ) from error

    GameApp().run()


if __name__ == "__main__":
    main()
