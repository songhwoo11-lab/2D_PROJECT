"""Shop scene placeholder that establishes the lobby entry and return contract."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_centered_text


SHOP_TITLE = "SHOP"
SHOP_NOTICE = "SHOP OPENING SOON"
SHOP_HINT = "PRESS ENTER : BACK TO LOBBY"
SHOP_TITLE_Y = SCREEN_HEIGHT - 200
SHOP_NOTICE_Y = SCREEN_HEIGHT - 300
SHOP_HINT_Y = 120


class ShopScene:
    """Temporary shop screen that returns to the lobby on the enter key."""

    def __init__(self, state=None, hud_font=None):
        self.state = state
        self.hud_font = hud_font
        self.keys = set()
        self.exit_requested = False
        self.pending_action = None

    def update(self, delta_time):
        return None

    def draw(self, draw_rectangle):
        draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            24,
            18,
            14,
            255,
            True,
        )
        if self.hud_font is None:
            return
        draw_centered_text(self.hud_font, SHOP_TITLE_Y, SHOP_TITLE, (255, 220, 100))
        draw_centered_text(self.hud_font, SHOP_NOTICE_Y, SHOP_NOTICE)
        draw_centered_text(self.hud_font, SHOP_HINT_Y, SHOP_HINT, (170, 190, 220))

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key in ("return", "enter", "q"):
            self.pending_action = "return_to_lobby"

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        return None

    def mouse_down(self, button, screen_x=None, screen_y=None):
        return None

    def mouse_up(self, button):
        return None

    def close(self):
        return None
