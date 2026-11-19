"""Shop screen with horizontally arranged gun cards."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import _measure_text_width as measure_text_width, draw_centered_text
from shop import (
    GUN_SHOP_ORDER,
    MAX_UPGRADE_LEVEL,
    gun_price,
    purchase_gun,
    purchase_result_message,
    upgrade_cost,
    upgrade_gun,
    upgrade_result_message,
)
from weapon import weapon_display_name


BUY_ACTION = 0
UPGRADE_ACTION = 1

SHOP_TITLE = "SHOP"
SHOP_NOTICE = "CLICK BUTTONS OR USE KEYS"
SHOP_HINT = "W/S GUN  A/D ACTION  SPACE EXECUTE  Q BACK"
BUY_LABEL = "구매"
OWNED_LABEL = "소지중"
UPGRADE_LABEL = "강화"
UPGRADE_DONE_LABEL = "강화완료"
EXIT_LABEL = "나가기"

SHOP_TITLE_Y = SCREEN_HEIGHT - 120
SHOP_COINS_Y = SCREEN_HEIGHT - 180
SHOP_NOTICE_Y = SCREEN_HEIGHT - 230
SHOP_RESULT_Y = SCREEN_HEIGHT - 280
SHOP_HINT_Y = 120

SHOP_CARD_WIDTH = 480
SHOP_CARD_GAP = 60
SHOP_CARD_LEFT = (
    SCREEN_WIDTH - (len(GUN_SHOP_ORDER) * SHOP_CARD_WIDTH + (len(GUN_SHOP_ORDER) - 1) * SHOP_CARD_GAP)
) // 2
SHOP_CARD_BOTTOM = 420
SHOP_CARD_TOP = 850
SHOP_NAME_Y = 800
SHOP_IMAGE_Y = 710
SHOP_LEVEL_Y = 620
SHOP_COST_Y = 555

SHOP_BUTTON_MARGIN = 30
SHOP_BUTTON_WIDTH = 190
SHOP_BUTTON_GAP = 40
SHOP_BUTTON_BOTTOM = 450
SHOP_BUTTON_TOP = 540
SHOP_BUTTON_TEXT_Y = 495

SHOP_EXIT_BUTTON = (SCREEN_WIDTH - 280, 60, SCREEN_WIDTH - 60, 160)

GUN_IMAGE_SIZES = {
    "pistol": (220, 125),
    "rifle": (280, 112),
    "machine_gun": (320, 78),
}


def draw_text_at(font, center_x, y, text, color=(255, 255, 255)):
    width = measure_text_width(font, text)
    font.draw(center_x - width / 2, y, text, color)


def card_rect(index):
    left = SHOP_CARD_LEFT + index * (SHOP_CARD_WIDTH + SHOP_CARD_GAP)
    return left, SHOP_CARD_BOTTOM, left + SHOP_CARD_WIDTH, SHOP_CARD_TOP


def button_rect(index, action):
    card_left = card_rect(index)[0]
    left = card_left + SHOP_BUTTON_MARGIN + action * (
        SHOP_BUTTON_WIDTH + SHOP_BUTTON_GAP
    )
    return left, SHOP_BUTTON_BOTTOM, left + SHOP_BUTTON_WIDTH, SHOP_BUTTON_TOP


def contains(rect, x, y):
    if x is None or y is None:
        return False
    left, bottom, right, top = rect
    return left <= x <= right and bottom <= y <= top


class ShopScene:
    """Shop card layout that keeps key and mouse controls in sync."""

    def __init__(self, state=None, hud_font=None, gun_images=None):
        self.state = state
        self.hud_font = hud_font
        self.gun_images = gun_images or {}
        self.keys = set()
        self.gun_index = 0
        self.action_index = BUY_ACTION
        self.last_result = None
        self.mouse_x = SCREEN_WIDTH / 2
        self.mouse_y = SCREEN_HEIGHT / 2
        self.hover_target = None
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
        self._draw_result()
        self._draw_cards(draw_rectangle)
        draw_centered_text(self.hud_font, SHOP_HINT_Y, SHOP_HINT, (170, 190, 220))
        self._draw_exit_button(draw_rectangle)

    def _draw_result(self):
        if self.last_result is None:
            return
        if hasattr(self.last_result, "level_before"):
            message = upgrade_result_message(self.last_result)
        else:
            message = purchase_result_message(self.last_result)
        draw_centered_text(self.hud_font, SHOP_RESULT_Y, message, (255, 160, 120))

    def _draw_cards(self, draw_rectangle):
        for index, gun_id in enumerate(GUN_SHOP_ORDER):
            left, bottom, right, top = card_rect(index)
            selected = index == self.gun_index
            name = weapon_display_name(gun_id)
            owned = self.state is not None and self.state.owns_gun(gun_id)
            level = self.state.upgrade_level(gun_id) if self.state is not None else 0
            center_x = (left + right) / 2

            draw_rectangle(left, bottom, right, top, 38, 40, 52, 255, True)
            if selected:
                draw_rectangle(left, bottom, right, top, 255, 220, 100, 255, False)

            draw_text_at(self.hud_font, center_x, SHOP_NAME_Y, name, (255, 220, 100))
            self._draw_gun_image(gun_id, center_x)
            draw_text_at(
                self.hud_font,
                center_x,
                SHOP_LEVEL_Y,
                "LV {}".format(level),
                (255, 255, 255),
            )

            costs = (
                "COIN {}".format(gun_price(gun_id)),
                "COIN MAX"
                if level >= MAX_UPGRADE_LEVEL
                else "COIN {}".format(upgrade_cost(gun_id, level)),
            )
            labels = (
                OWNED_LABEL if owned else BUY_LABEL,
                UPGRADE_DONE_LABEL if level >= MAX_UPGRADE_LEVEL else UPGRADE_LABEL,
            )
            for action in (BUY_ACTION, UPGRADE_ACTION):
                self._draw_button(draw_rectangle, index, action)
                button_left = button_rect(index, action)[0]
                button_center_x = button_left + SHOP_BUTTON_WIDTH / 2
                draw_text_at(
                    self.hud_font,
                    button_center_x,
                    SHOP_COST_Y,
                    costs[action],
                    (255, 220, 100),
                )
                draw_text_at(
                    self.hud_font,
                    button_center_x,
                    SHOP_BUTTON_TEXT_Y,
                    labels[action],
                    (255, 255, 255),
                )

    def _draw_gun_image(self, gun_id, center_x):
        image = self.gun_images.get(gun_id)
        if image is None:
            draw_text_at(
                self.hud_font,
                center_x,
                SHOP_IMAGE_Y,
                "[{}]".format(weapon_display_name(gun_id)),
                (170, 190, 220),
            )
            return
        width, height = GUN_IMAGE_SIZES[gun_id]
        image.draw(center_x, SHOP_IMAGE_Y, width, height)

    def _draw_button(self, draw_rectangle, index, action):
        left, bottom, right, top = button_rect(index, action)
        selected = index == self.gun_index and action == self.action_index
        hovered = self.hover_target == ("button", index, action)
        if selected:
            color = (220, 170, 60)
        elif hovered:
            color = (90, 120, 150)
        else:
            color = (62, 74, 96)
        draw_rectangle(left, bottom, right, top, *color, 255, True)

    def _draw_exit_button(self, draw_rectangle):
        left, bottom, right, top = SHOP_EXIT_BUTTON
        hovered = self.hover_target == ("exit",)
        color = (190, 80, 70) if hovered else (130, 60, 55)
        draw_rectangle(left, bottom, right, top, *color, 255, True)
        draw_text_at(
            self.hud_font,
            (left + right) / 2,
            (bottom + top) / 2,
            EXIT_LABEL,
            (255, 255, 255),
        )

    def _execute_action(self):
        if self.state is None:
            return
        gun_id = GUN_SHOP_ORDER[self.gun_index]
        if self.action_index == BUY_ACTION:
            self.last_result = purchase_gun(self.state, gun_id)
        else:
            self.last_result = upgrade_gun(self.state, gun_id)

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
            self.action_index = BUY_ACTION
        elif key in ("d", "right"):
            self.action_index = UPGRADE_ACTION
        elif key == "space":
            self._execute_action()
        elif key in ("q", "return"):
            self.pending_action = "return_to_lobby"

    def key_up(self, key):
        self.keys.discard(key.lower())

    def _target_at(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        if contains(SHOP_EXIT_BUTTON, screen_x, canvas_y):
            return ("exit",)
        for index in range(len(GUN_SHOP_ORDER)):
            for action in (BUY_ACTION, UPGRADE_ACTION):
                if contains(button_rect(index, action), screen_x, canvas_y):
                    return ("button", index, action)
            if contains(card_rect(index), screen_x, canvas_y):
                return ("card", index)
        return None

    def mouse_move(self, screen_x, screen_y):
        self.mouse_x = screen_x
        self.mouse_y = screen_y
        self.hover_target = self._target_at(screen_x, screen_y)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if button != "left" or screen_x is None or screen_y is None:
            return
        target = self._target_at(screen_x, screen_y)
        if target is None:
            return
        if target[0] == "exit":
            self.pending_action = "return_to_lobby"
        elif target[0] == "card":
            self.gun_index = target[1]
        elif target[0] == "button":
            self.gun_index = target[1]
            self.action_index = target[2]
            self._execute_action()

    def mouse_up(self, button):
        return None

    def close(self):
        return None
