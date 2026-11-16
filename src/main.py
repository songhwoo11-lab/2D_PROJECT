"""Pico2D entry point that runs the lobby and the battle scenes."""

from pathlib import Path

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
from lobby_scene import LobbyScene
from player import Player
from weapon import Gun


ASSET_DIRECTORY = Path(__file__).resolve().parent.parent / "image"


class GameApp:
    """Loads the shared assets and keeps the currently active scene."""

    def __init__(self):
        self.assets = {}
        self.state = GameState()
        self.scene = None
        self.scene_kind = None
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
        )

    def create_battle_scene(self):
        player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=self.assets["player_image"],
        )
        return BattleScene(
            player,
            Gun(),
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
            total_waves=development_total_waves(),
            wave_spawn_rate=development_spawn_rate(),
        )

    def switch_scene(self, kind):
        if self.scene is not None:
            self.scene.close()
        if kind == "lobby":
            self.scene = self.create_lobby_scene()
        elif kind == "battle":
            self.scene = self.create_battle_scene()
        else:
            raise ValueError("unknown scene: {}".format(kind))
        self.scene_kind = kind

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
                pico2d.SDLK_q: "q",
                pico2d.SDLK_UP: "up",
                pico2d.SDLK_DOWN: "down",
                pico2d.SDLK_RETURN: "return",
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
                            self.running = False
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
                pico2d.clear_canvas()
                self.scene.draw(pico2d.draw_rectangle)
                pico2d.update_canvas()
                if self.scene.exit_requested:
                    self.running = False
                frame_duration = pico2d.get_time() - frame_start
                pico2d.delay(max(0.0, FRAME_TIME - frame_duration))
                last_time = frame_start
        finally:
            if self.scene is not None:
                self.scene.close()
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
