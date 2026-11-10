import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import main
import enemy_types
from enemy import EnemyType


class FakeImage:
    texture = object()

    def draw(self, *args):
        pass

    def rotate_draw(self, *args):
        pass

    def composite_draw(self, *args):
        pass


class FakeFont:
    def draw(self, *args):
        pass


class MainTests(unittest.TestCase):
    def test_main_initializes_loads_assets_renders_and_closes(self):
        loaded_images = []
        opened_canvases = []
        closed = []
        delays = []
        loaded_fonts = []
        events = [SimpleNamespace(type=1)]

        def draw_rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
            pass

        def draw_line(x1, y1, x2, y2, r=0, g=0, b=0, a=255):
            pass

        def load_image(path):
            loaded_images.append(path)
            return FakeImage()

        def load_font(path, size):
            loaded_fonts.append((path, size))
            return FakeFont()

        pico2d = SimpleNamespace(
            SDL_QUIT=1,
            SDL_KEYDOWN=2,
            SDL_KEYUP=3,
            SDL_MOUSEMOTION=4,
            SDL_MOUSEBUTTONDOWN=5,
            SDL_MOUSEBUTTONUP=6,
            SDL_BUTTON_LEFT=1,
            SDLK_ESCAPE=27,
            SDLK_F1=0x4000003A,
            SDLK_w=ord("w"),
            SDLK_a=ord("a"),
            SDLK_s=ord("s"),
            SDLK_d=ord("d"),
            SDLK_e=ord("e"),
            SDLK_r=ord("r"),
            open_canvas=lambda *args: opened_canvases.append(args),
            close_canvas=lambda: closed.append(True),
            load_image=load_image,
            load_font=load_font,
            get_time=lambda: 0.0,
            get_events=lambda: events,
            clear_canvas=lambda: None,
            update_canvas=lambda: None,
            delay=lambda duration: delays.append(duration),
            draw_line=draw_line,
            draw_rectangle=draw_rectangle,
            draw_circle=lambda *args: None,
        )

        with patch.dict(sys.modules, {"pico2d": pico2d}):
            with patch("hud._measure_text_width", return_value=100):
                with patch.object(
                    enemy_types.pico2d,
                    "SDL_SetTextureBlendMode",
                    return_value=0,
                ), patch.object(
                    enemy_types.pico2d,
                    "SDL_SetTextureAlphaMod",
                    return_value=0,
                ):
                    main.main()

        self.assertEqual(opened_canvases, [(800, 600)])
        self.assertEqual(
            main.ASSET_DIRECTORY,
            Path(main.__file__).resolve().parent.parent / "image",
        )
        self.assertEqual(
            [path.rsplit("\\", 1)[-1] for path in loaded_images],
            [
                "in_game.png",
                "boy.png",
                "gun.png",
                "bullet.png",
                "arrow.png",
                "common_skel.png",
                "boom skel.png",
                "tanker_skel.png",
                "assassin_skel.png",
                "bow_skel.png",
            ],
        )
        self.assertTrue(
            all(Path(path).parent == main.ASSET_DIRECTORY for path in loaded_images)
        )
        self.assertTrue(all(Path(path).is_file() for path in loaded_images))
        self.assertEqual(
            [(path.rsplit("\\", 2)[-2:], size) for path, size in loaded_fonts],
            [
                (["font", "PuzzleSansSuper.ttf"], 20),
                (["font", "PuzzleSansSuper.ttf"], 15),
            ],
        )
        self.assertTrue(Path(loaded_fonts[0][0]).is_file())
        self.assertEqual(closed, [True])
        self.assertEqual(len(delays), 1)


if __name__ == "__main__":
    unittest.main()
