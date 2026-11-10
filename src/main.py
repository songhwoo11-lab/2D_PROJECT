"""Pico2D entry point for the first-stage playable battle loop."""

from pathlib import Path

from battle_scene import BattleScene
from enemy import EnemyType
from game_config import (
    FRAME_TIME,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from player import Player
from weapon import Gun


ASSET_DIRECTORY = Path(__file__).resolve().parent.parent / "image"


def main():
    try:
        import pico2d
    except ModuleNotFoundError as error:
        if error.name != "pico2d":
            raise
        raise RuntimeError(
            "Pico2D is required to run the game. Install Pico2D in this Python environment."
        ) from error

    pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    scene = None
    try:
        background = pico2d.load_image(str(ASSET_DIRECTORY / "in_game.png"))
        player_image = pico2d.load_image(str(ASSET_DIRECTORY / "boy.png"))
        gun_image = pico2d.load_image(str(ASSET_DIRECTORY / "gun.png"))
        bullet_image = pico2d.load_image(str(ASSET_DIRECTORY / "bullet.png"))
        arrow_image = pico2d.load_image(str(ASSET_DIRECTORY / "arrow.png"))
        hud_font = pico2d.load_font(
            str(ASSET_DIRECTORY / "font" / "PuzzleSansSuper.ttf"),
            20,
        )
        enemy_images = {
            EnemyType.BASIC: pico2d.load_image(
                str(ASSET_DIRECTORY / "common_skel.png")
            ),
            EnemyType.EXPLOSIVE: pico2d.load_image(
                str(ASSET_DIRECTORY / "boom skel.png")
            ),
            EnemyType.TANKER: pico2d.load_image(
                str(ASSET_DIRECTORY / "tanker_skel.png")
            ),
            EnemyType.ASSASSIN: pico2d.load_image(
                str(ASSET_DIRECTORY / "assassin_skel.png")
            ),
            EnemyType.ARCHER: pico2d.load_image(
                str(ASSET_DIRECTORY / "bow_skel.png")
            ),
        }
        player = Player(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
            image=player_image,
        )
        scene = BattleScene(
            player,
            Gun(),
            background,
            gun_image=gun_image,
            bullet_image=bullet_image,
            hud_font=hud_font,
            enemy_images=enemy_images,
            enemy_draw_rectangle=pico2d.draw_rectangle,
            enemy_draw_circle=pico2d.draw_circle,
            arrow_image=arrow_image,
        )
        scene.spawn_test_enemies()
        key_map = {
            pico2d.SDLK_F1: "f1",
            pico2d.SDLK_w: "w",
            pico2d.SDLK_a: "a",
            pico2d.SDLK_s: "s",
            pico2d.SDLK_d: "d",
            pico2d.SDLK_e: "e",
            pico2d.SDLK_r: "r",
        }

        running = True
        last_time = pico2d.get_time()
        while running:
            frame_start = pico2d.get_time()
            delta_time = min(max(frame_start - last_time, 0.0), 0.1)
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    running = False
                elif event.type == pico2d.SDL_KEYDOWN:
                    if event.key == pico2d.SDLK_ESCAPE:
                        running = False
                    elif event.key in key_map:
                        scene.key_down(key_map[event.key])
                elif event.type == pico2d.SDL_KEYUP:
                    if event.key in key_map:
                        scene.key_up(key_map[event.key])
                elif event.type == pico2d.SDL_MOUSEMOTION:
                    scene.mouse_move(event.x, event.y)
                elif event.type == pico2d.SDL_MOUSEBUTTONDOWN:
                    if event.button == pico2d.SDL_BUTTON_LEFT:
                        scene.mouse_down("left", event.x, event.y)
                elif event.type == pico2d.SDL_MOUSEBUTTONUP:
                    if event.button == pico2d.SDL_BUTTON_LEFT:
                        scene.mouse_up("left")

            scene.update(delta_time)
            pico2d.clear_canvas()
            scene.draw(pico2d.draw_rectangle)
            pico2d.update_canvas()
            frame_duration = pico2d.get_time() - frame_start
            pico2d.delay(max(0.0, FRAME_TIME - frame_duration))
            last_time = frame_start
    finally:
        if scene is not None:
            scene.close()
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
