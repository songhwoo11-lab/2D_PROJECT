"""Shop scene placeholder that establishes the lobby entry and return contract."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_centered_text
from shop import GUN_SHOP_ORDER, gun_price, purchase_gun, upgrade_gun
from weapon import weapon_display_name


SHOP_TITLE = "SHOP"
SHOP_NOTICE = "SHOP OPENING SOON"
SHOP_HINT = "W/S GUN  A/D ACTION  SPACE EXECUTE  Q BACK"
SHOP_TITLE_Y = SCREEN_HEIGHT - 200
SHOP_COINS_Y = SCREEN_HEIGHT - 260
SHOP_NOTICE_Y = SCREEN_HEIGHT - 300
SHOP_HINT_Y = 120
SHOP_ROW_TOP_Y = 800
SHOP_ROW_SPACING = 60


class ShopScene:
    """Temporary shop screen that returns to the lobby on the enter key."""

    def __init__(self, state=None, hud_font=None):
        self.state = state
        self.hud_font = hud_font
        self.keys = set()
        self.gun_index = 0
        self.action_index = 0
        self.last_result = None
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
        if self.state is not None:
            draw_centered_text(
                self.hud_font,
                SHOP_COINS_Y,
                "COINS {}".format(self.state.coins),
                (255, 220, 100),
            )
        draw_centered_text(self.hud_font, SHOP_NOTICE_Y, SHOP_NOTICE)
        self._draw_gun_rows()
        draw_centered_text(self.hud_font, SHOP_HINT_Y, SHOP_HINT, (170, 190, 220))

    def _draw_gun_rows(self):
        for index, gun_id in enumerate(GUN_SHOP_ORDER):
            owned = self.state is not None and gun_id in self.state.owned_guns
            label = "{} | PRICE {} | {}".format(
                weapon_display_name(gun_id),
                gun_price(gun_id),
                "OWNED" if owned else "NOT OWNED",
            )
            draw_centered_text(
                self.hud_font,
                SHOP_ROW_TOP_Y - index * SHOP_ROW_SPACING,
                label,
            )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key in ("w", "up"):
            self.gun_index = (self.gun_index - 1) % len(GUN_SHOP_ORDER)
        elif key in ("s", "down"):
            self.gun_index = (self.gun_index + 1) % len(GUN_SHOP_ORDER)
        elif key in ("a", "left"):
            self.action_index = 0
        elif key in ("d", "right"):
            self.action_index = 1
        elif key == "space" and self.state is not None:
            gun_id = GUN_SHOP_ORDER[self.gun_index]
            if self.action_index == 0:
                self.last_result = purchase_gun(self.state, gun_id)
            else:
                self.last_result = upgrade_gun(self.state, gun_id)
        elif key in ("q", "return"):
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
