"""Pico2D entry point that runs the lobby and the battle scenes."""

from pathlib import Path

import pico2d

from battle_record import BattleRecord
from battle_scene import DEBUG_FONT_SIZE, SHOT_FEEDBACK_FONT_SIZE, BattleScene
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
from lobby_map import LOBBY_START_KEY
from lobby_scene import LobbyScene
from player import Player
from shop_scene import ShopScene
from training_scene import TrainingScene
from weapon import Gun


ASSET_DIRECTORY = Path(__file__).resolve().parent.parent / "image"


class GameApp:
    """Loads the shared assets and keeps the currently active scene."""

    def __init__(self):
        self.assets = {}
        self.state = GameState()
        self.scene = None
        self.scene_kind = None
        self.lobby_node_key = LOBBY_START_KEY
        self.cursor_hidden = False
        self.running = True

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
        self.assets["gun_image"] = pico2d.load_image(str(directory / "gun.png"))
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
        )

    def create_battle_scene(self):
        player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=self.assets["player_image"],
        )
        return BattleScene(
            player,
            Gun.from_gun_id(self.state.selected_gun),
            self.assets["battle_background"],
            gun_image=self.assets["gun_image"],
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
            total_waves=development_total_waves(),
            wave_spawn_rate=development_spawn_rate(),
        )

    def switch_scene(self, kind):
        if self.scene_kind == "lobby" and self.scene is not None:
            self.lobby_node_key = getattr(
                self.scene, "current_node", LOBBY_START_KEY
            )
        if self.scene is not None:
            self.scene.close()
        if kind == "lobby":
            self.scene = self.create_lobby_scene()
        elif kind == "battle":
            self.scene = self.create_battle_scene()
        elif kind == "shop":
            self.scene = self.create_shop_scene()
        elif kind == "training":
            self.scene = self.create_training_scene()
        else:
            raise ValueError("unknown scene: {}".format(kind))
        self.scene_kind = kind

    def create_shop_scene(self):
        return ShopScene(
            state=self.state,
            hud_font=self.assets["hud_font"],
        )

    def create_training_scene(self):
        player = Player(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            image=self.assets["player_image"],
        )
        return TrainingScene(
            player=player,
            gun=Gun.from_gun_id(self.state.selected_gun),
            background=self.assets.get("training_background"),
            hud_font=self.assets["hud_font"],
            state=self.state,
            target_image=self.assets.get("training_target_image"),
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
        if action == "return_to_lobby":
            self.switch_scene("lobby")
            return True
        raise ValueError("unknown scene action: {}".format(action))

    def handle_scene_exit(self):
        """Handle the active scene's request to leave the game."""
        if self.scene_kind == "battle":
            self.handle_battle_exit()
            return
        self.running = False

    def handle_escape_key(self):
        if self.scene_kind == "lobby":
            self.running = False
            return
        self.scene.key_down("escape")

    def update_cursor_visibility(self):
        should_hide = not bool(getattr(self.scene, "shows_system_cursor", True))
        if should_hide == self.cursor_hidden:
            return
        if should_hide:
            pico2d.hide_cursor()
        else:
            pico2d.show_cursor()
        self.cursor_hidden = should_hide

    def handle_battle_exit(self):
        """Store the finished battle result and go back to the lobby."""
        battle = self.scene
        self.state.coins += battle.coins
        self.state.add_record(
            BattleRecord(
                result=battle.result.value,
                reached_wave=battle.reached_wave,
                elapsed_time=battle.elapsed_time,
                clear_time=battle.clear_time,
            )
        )
        self.switch_scene("lobby")

    def run(self):
        import pico2d

        pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
        try:
            self.load_assets()
            self.switch_scene("lobby")
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
                pico2d.SDLK_RETURN: "return",
                pico2d.SDLK_ESCAPE: "escape",
            }

            last_time = pico2d.get_time()
            while self.running:
                frame_start = pico2d.get_time()
                delta_time = min(max(frame_start - last_time, 0.0), 0.1)
                for event in pico2d.get_events():
                    if event.type == pico2d.SDL_QUIT:
                        self.running = False
                    elif event.type == pico2d.SDL_KEYDOWN:
                        if event.key == pico2d.SDLK_ESCAPE:
                            self.handle_escape_key()
                        elif event.key in key_map:
                            self.scene.key_down(key_map[event.key])
                    elif event.type == pico2d.SDL_KEYUP:
                        if event.key in key_map:
                            self.scene.key_up(key_map[event.key])
                    elif event.type == pico2d.SDL_MOUSEMOTION:
                        self.scene.mouse_move(event.x, event.y)
                    elif event.type == pico2d.SDL_MOUSEBUTTONDOWN:
                        if event.button == pico2d.SDL_BUTTON_LEFT:
                            self.scene.mouse_down("left", event.x, event.y)
                    elif event.type == pico2d.SDL_MOUSEBUTTONUP:
                        if event.button == pico2d.SDL_BUTTON_LEFT:
                            self.scene.mouse_up("left")

                self.scene.update(delta_time)
                self.handle_scene_action()
                pico2d.clear_canvas()
                self.scene.draw(pico2d.draw_rectangle)
                self.update_cursor_visibility()
                pico2d.update_canvas()
                if self.scene.exit_requested:
                    self.handle_scene_exit()
                frame_duration = pico2d.get_time() - frame_start
                pico2d.delay(max(0.0, FRAME_TIME - frame_duration))
                last_time = frame_start
        finally:
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
