import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import main


class FakeImage:
    def draw(self, *args):
        pass

    def rotate_draw(self, *args):
        pass

    def composite_draw(self, *args):
        pass


class MainTests(unittest.TestCase):
    def test_main_initializes_loads_assets_renders_and_closes(self):
        loaded_images = []
        opened_canvases = []
        closed = []
        delays = []
        events = [SimpleNamespace(type=1)]

        def draw_rectangle(x1, y1, x2, y2, r=255, g=0, b=0, a=255, filled=False):
            pass

        def draw_line(x1, y1, x2, y2, r=0, g=0, b=0, a=255):
            pass

        def load_image(path):
            loaded_images.append(path)
            return FakeImage()

        pico2d = SimpleNamespace(
            SDL_QUIT=1,
            SDL_KEYDOWN=2,
            SDL_KEYUP=3,
            SDL_MOUSEMOTION=4,
            SDL_MOUSEBUTTONDOWN=5,
            SDL_MOUSEBUTTONUP=6,
            SDL_BUTTON_LEFT=1,
            SDLK_ESCAPE=27,
            SDLK_w=ord("w"),
            SDLK_a=ord("a"),
            SDLK_s=ord("s"),
            SDLK_d=ord("d"),
            SDLK_e=ord("e"),
            SDLK_r=ord("r"),
            open_canvas=lambda *args: opened_canvases.append(args),
            close_canvas=lambda: closed.append(True),
            load_image=load_image,
            get_time=lambda: 0.0,
            get_events=lambda: events,
            clear_canvas=lambda: None,
            update_canvas=lambda: None,
            delay=lambda duration: delays.append(duration),
            draw_line=draw_line,
            draw_rectangle=draw_rectangle,
        )

        with patch.dict(sys.modules, {"pico2d": pico2d}):
            main.main()

        self.assertEqual(opened_canvases, [(800, 600)])
        self.assertEqual(
            [path.rsplit("\\", 1)[-1] for path in loaded_images],
            ["in_game.png", "boy.png", "gun.png", "bullet.png"],
        )
        self.assertEqual(closed, [True])
        self.assertEqual(len(delays), 1)


if __name__ == "__main__":
    unittest.main()
