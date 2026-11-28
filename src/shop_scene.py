"""Shop screen with horizontally arranged gun cards."""

from audio import (
    BUY_GUN_SOUND_FILE,
    BUY_UPGRADE_FAIL_SOUND_FILE,
    GUN_LEVEL_DOWN_SOUND_FILE,
    GUN_LEVEL_EXPLOSION_SOUND_FILE,
    GUN_LEVEL_FAIL_SOUND_FILE,
    GUN_LEVEL_UP_SOUND_FILE,
)
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import _measure_text_width as measure_text_width, draw_centered_text
from shop import (
    GUN_SHOP_ORDER,
    MAX_UPGRADE_LEVEL,
    PurchaseResult,
    UpgradeResult,
    gun_price,
    purchase_gun,
    purchase_result_message,
    upgrade_cost,
    upgrade_gun,
    upgrade_result_message,
    upgrade_chances,
)
from weapon import weapon_display_name, weapon_stats_at_level


NO_ACTION = -1
BUY_ACTION = 0
UPGRADE_ACTION = 1
STATE_ACTION = 2

UPGRADE_SOUND_BY_RESULT = {
    UpgradeResult.SUCCESS: GUN_LEVEL_UP_SOUND_FILE,
    UpgradeResult.FAILURE: GUN_LEVEL_FAIL_SOUND_FILE,
    UpgradeResult.DOWNGRADE: GUN_LEVEL_DOWN_SOUND_FILE,
    UpgradeResult.DESTROY: GUN_LEVEL_EXPLOSION_SOUND_FILE,
}

SHOP_TITLE = "SHOP"
BUY_LABEL = "BUY"
OWNED_LABEL = "OWNED"
UPGRADE_LABEL = "UPGRADE"
UPGRADE_DONE_LABEL = "MAXED"
STATE_LABEL = "State"
EXIT_LABEL = "EXIT"

SHOP_TITLE_Y = SCREEN_HEIGHT - 120
SHOP_COINS_Y = SCREEN_HEIGHT - 180
SHOP_RESULT_Y = SCREEN_HEIGHT - 280

SHOP_SELECTED_SLOT_SIZE = (472, 508)
SHOP_UNSELECTED_SLOT_SIZE = (464, 509)
SHOP_CARD_WIDTH = max(SHOP_SELECTED_SLOT_SIZE[0], SHOP_UNSELECTED_SLOT_SIZE[0])
SHOP_CARD_HEIGHT = max(SHOP_SELECTED_SLOT_SIZE[1], SHOP_UNSELECTED_SLOT_SIZE[1])
SHOP_CARD_GAP = 60
SHOP_CARD_LEFT = (
    SCREEN_WIDTH - (len(GUN_SHOP_ORDER) * SHOP_CARD_WIDTH + (len(GUN_SHOP_ORDER) - 1) * SHOP_CARD_GAP)
) // 2
SHOP_CARD_BOTTOM = 320
SHOP_CARD_TOP = SHOP_CARD_BOTTOM + SHOP_CARD_HEIGHT
SHOP_NAME_Y = SHOP_CARD_TOP - 48
SHOP_IMAGE_Y = SHOP_CARD_TOP - 124
SHOP_LEVEL_Y = SHOP_CARD_TOP - 194
SHOP_COST_Y = SHOP_CARD_TOP - 245

SHOP_BUTTON_MARGIN = 28
SHOP_BUTTON_WIDTH = 183
SHOP_BUTTON_GAP = 50
SHOP_BUTTON_BOTTOM = SHOP_CARD_BOTTOM + 138
SHOP_BUTTON_TOP = SHOP_CARD_BOTTOM + 219
SHOP_BUTTON_TEXT_Y = (SHOP_BUTTON_BOTTOM + SHOP_BUTTON_TOP) // 2

SHOP_STATE_BUTTON_WIDTH = SHOP_CARD_WIDTH - SHOP_BUTTON_MARGIN * 2 - 5
SHOP_STATE_BUTTON_BOTTOM = SHOP_CARD_BOTTOM + 32
SHOP_STATE_BUTTON_TOP = SHOP_CARD_BOTTOM + 113
SHOP_STATE_BUTTON_TEXT_Y = (SHOP_STATE_BUTTON_BOTTOM + SHOP_STATE_BUTTON_TOP) // 2

SHOP_EXIT_BUTTON = (SCREEN_WIDTH - 280, 60, SCREEN_WIDTH - 60, 160)

STATE_PANEL_WIDTH = 760
STATE_PANEL_BOTTOM = 450
STATE_PANEL_TOP = 900
STATE_PANEL_TITLE_Y = 850
STATE_PANEL_ROW_TOP = 790
STATE_PANEL_ROW_GAP = 50

UPGRADE_MODAL_RECT = (180, 100, 1620, 1100)
UPGRADE_MODAL_TITLE_Y = 1040
UPGRADE_MODAL_SIDE_BOTTOM = 440
UPGRADE_MODAL_SIDE_TOP = 970
UPGRADE_MODAL_LEFT_RECT = (220, 440, 850, 970)
UPGRADE_MODAL_RIGHT_RECT = (950, 440, 1580, 970)
UPGRADE_MODAL_SIDE_TITLE_Y = 920
UPGRADE_MODAL_ROW_TOP = 860
UPGRADE_MODAL_ROW_GAP = 50
UPGRADE_MODAL_ARROW_Y = 705
UPGRADE_MODAL_CHANCE_Y = 370
UPGRADE_MODAL_CHANCE_DETAIL_Y = 310
UPGRADE_MODAL_BUTTON_BOTTOM = 150
UPGRADE_MODAL_BUTTON_TOP = 250
UPGRADE_MODAL_BUTTON_TEXT_Y = 200
UPGRADE_MODAL_BUTTON_WIDTH = 260
UPGRADE_MODAL_BUTTON_GAP = 80
UPGRADE_CHANGED_COLOR = (80, 255, 80)

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
    if action == STATE_ACTION:
        left = card_left + (SHOP_CARD_WIDTH - SHOP_STATE_BUTTON_WIDTH) // 2
        return (
            left,
            SHOP_STATE_BUTTON_BOTTOM,
            left + SHOP_STATE_BUTTON_WIDTH,
            SHOP_STATE_BUTTON_TOP,
        )
    left = card_left + SHOP_BUTTON_MARGIN + action * (
        SHOP_BUTTON_WIDTH + SHOP_BUTTON_GAP
    )
    return left, SHOP_BUTTON_BOTTOM, left + SHOP_BUTTON_WIDTH, SHOP_BUTTON_TOP


def state_panel_rect():
    left = (SCREEN_WIDTH - STATE_PANEL_WIDTH) // 2
    return left, STATE_PANEL_BOTTOM, left + STATE_PANEL_WIDTH, STATE_PANEL_TOP


def upgrade_modal_rect():
    return UPGRADE_MODAL_RECT


def upgrade_confirm_rect():
    total_width = UPGRADE_MODAL_BUTTON_WIDTH * 2 + UPGRADE_MODAL_BUTTON_GAP
    left = (SCREEN_WIDTH - total_width) // 2
    return (
        left,
        UPGRADE_MODAL_BUTTON_BOTTOM,
        left + UPGRADE_MODAL_BUTTON_WIDTH,
        UPGRADE_MODAL_BUTTON_TOP,
    )


def upgrade_cancel_rect():
    confirm = upgrade_confirm_rect()
    gap = UPGRADE_MODAL_BUTTON_GAP
    left = confirm[0] + UPGRADE_MODAL_BUTTON_WIDTH + gap
    return (
        left,
        confirm[1],
        left + UPGRADE_MODAL_BUTTON_WIDTH,
        confirm[3],
    )


def contains(rect, x, y):
    if x is None or y is None:
        return False
    left, bottom, right, top = rect
    return left <= x <= right and bottom <= y <= top


def purchase_available(state, gun_id):
    return state is None or not state.owns_gun(gun_id)


def upgrade_available(state, gun_id):
    return (
        state is not None
        and state.owns_gun(gun_id)
        and state.upgrade_level(gun_id) < MAX_UPGRADE_LEVEL
    )


def state_available(state, gun_id):
    return True


def stat_rows(gun_id, level):
    spec = weapon_stats_at_level(gun_id, level)
    return (
        ("NAME", spec.name.upper()),
        ("LEVEL", str(level)),
        ("DAMAGE", str(spec.damage)),
        ("FIRE INTERVAL", "{:.3f}s".format(spec.fire_interval_seconds)),
        ("RELOAD TIME", "{:.1f}s".format(spec.reload_seconds)),
        ("MAX TEMP", "{:.1f}".format(spec.temperature_limit)),
        ("MAGAZINE SIZE", str(spec.magazine_size)),
    )


class ShopScene:
    """Shop card layout that keeps key and mouse controls in sync."""

    def __init__(
        self,
        state=None,
        hud_font=None,
        gun_images=None,
        background=None,
        selected_slot_image=None,
        unselected_slot_image=None,
        audio=None,
    ):
        self.state = state
        self.audio = audio
        self.hud_font = hud_font
        self.gun_images = gun_images or {}
        self.background = background
        self.selected_slot_image = selected_slot_image
        self.unselected_slot_image = unselected_slot_image
        self.keys = set()
        self.gun_index = 0
        self.action_index = BUY_ACTION
        self._select_first_available_action()
        self.last_result = None
        self.mouse_x = SCREEN_WIDTH / 2
        self.mouse_y = SCREEN_HEIGHT / 2
        self.hover_target = None
        self.state_panel_gun_id = None
        self.upgrade_modal_gun_id = None
        self.exit_requested = False
        self.pending_action = None

    def _action_available(self, index, action):
        gun_id = GUN_SHOP_ORDER[index]
        if action == BUY_ACTION:
            return purchase_available(self.state, gun_id)
        if action == UPGRADE_ACTION:
            return upgrade_available(self.state, gun_id)
        return state_available(self.state, gun_id)

    def _available_actions(self):
        return tuple(
            action
            for action in (BUY_ACTION, UPGRADE_ACTION, STATE_ACTION)
            if self._action_available(self.gun_index, action)
        )

    def _normalize_action(self):
        available = self._available_actions()
        if self.action_index not in available:
            self.action_index = available[0] if available else NO_ACTION

    def _select_first_available_action(self):
        available = self._available_actions()
        self.action_index = available[0] if available else NO_ACTION

    def _hide_state_panel(self):
        self.state_panel_gun_id = None

    def _hide_upgrade_modal(self):
        self.upgrade_modal_gun_id = None

    def update(self, delta_time):
        return None

    def draw(self, draw_rectangle):
        if self.background is not None:
            self.background.draw(
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
        else:
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
        self._draw_result()
        self._draw_cards(draw_rectangle)
        self._draw_state_panel(draw_rectangle)
        self._draw_exit_button(draw_rectangle)
        self._draw_upgrade_modal(draw_rectangle)

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
            center_y = (bottom + top) / 2

            slot_image = (
                self.selected_slot_image if selected else self.unselected_slot_image
            )
            if slot_image is not None:
                slot_size = (
                    SHOP_SELECTED_SLOT_SIZE if selected else SHOP_UNSELECTED_SLOT_SIZE
                )
                slot_image.draw(center_x, center_y, *slot_size)
            else:
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
                available = self._action_available(index, action)
                self._draw_button(draw_rectangle, index, action, available)
                button_left = button_rect(index, action)[0]
                button_center_x = button_left + SHOP_BUTTON_WIDTH / 2
                cost_color = (255, 220, 100) if available else (110, 110, 110)
                label_color = (255, 255, 255) if available else (110, 110, 110)
                draw_text_at(
                    self.hud_font,
                    button_center_x,
                    SHOP_COST_Y,
                    costs[action],
                    cost_color,
                )
                draw_text_at(
                    self.hud_font,
                    button_center_x,
                    SHOP_BUTTON_TEXT_Y,
                    labels[action],
                    label_color,
                )

            self._draw_button(draw_rectangle, index, STATE_ACTION, True)
            draw_text_at(
                self.hud_font,
                center_x,
                SHOP_STATE_BUTTON_TEXT_Y,
                STATE_LABEL,
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

    def _draw_button(self, draw_rectangle, index, action, available):
        left, bottom, right, top = button_rect(index, action)
        selected = available and index == self.gun_index and action == self.action_index
        hovered = available and self.hover_target == ("button", index, action)
        if not available:
            color = (35, 40, 50)
        elif selected:
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

    def _state_panel_rows(self):
        gun_id = self.state_panel_gun_id
        level = self.state.upgrade_level(gun_id) if self.state is not None else 0
        return stat_rows(gun_id, level)

    def _draw_state_panel(self, draw_rectangle):
        if self.state_panel_gun_id is None:
            return
        left, bottom, right, top = state_panel_rect()
        center_x = (left + right) / 2
        gun_id = self.state_panel_gun_id

        draw_rectangle(
            left,
            bottom,
            right,
            top,
            20,
            24,
            34,
            245,
            True,
        )
        draw_rectangle(
            left,
            bottom,
            right,
            top,
            255,
            220,
            100,
            255,
            False,
        )
        draw_text_at(
            self.hud_font,
            center_x,
            STATE_PANEL_TITLE_Y,
            "STATE - {}".format(weapon_display_name(gun_id)),
            (255, 220, 100),
        )
        for row_index, (label, value) in enumerate(self._state_panel_rows()):
            draw_text_at(
                self.hud_font,
                center_x,
                STATE_PANEL_ROW_TOP - row_index * STATE_PANEL_ROW_GAP,
                "{} {}".format(label, value),
            )

    def _draw_upgrade_side(self, draw_rectangle, rect, title, rows, changed_indices):
        left, bottom, right, top = rect
        center_x = (left + right) / 2
        draw_rectangle(left, bottom, right, top, 30, 35, 50, 255, True)
        draw_rectangle(left, bottom, right, top, 90, 110, 140, 255, False)
        draw_text_at(self.hud_font, center_x, UPGRADE_MODAL_SIDE_TITLE_Y, title, (255, 220, 100))
        for row_index, (label, value) in enumerate(rows):
            color = UPGRADE_CHANGED_COLOR if row_index in changed_indices else (255, 255, 255)
            draw_text_at(
                self.hud_font,
                center_x,
                UPGRADE_MODAL_ROW_TOP - row_index * UPGRADE_MODAL_ROW_GAP,
                "{} {}".format(label, value),
                color,
            )

    def _draw_upgrade_modal(self, draw_rectangle):
        if self.upgrade_modal_gun_id is None:
            return
        gun_id = self.upgrade_modal_gun_id
        level = self.state.upgrade_level(gun_id) if self.state is not None else 0
        after_level = min(level + 1, MAX_UPGRADE_LEVEL)
        chances = upgrade_chances(level)
        before_rows = stat_rows(gun_id, level)
        after_rows = stat_rows(gun_id, after_level)
        changed_indices = {
            index
            for index, (before, after) in enumerate(zip(before_rows, after_rows))
            if before != after
        }

        left, bottom, right, top = upgrade_modal_rect()
        draw_rectangle(left, bottom, right, top, 18, 22, 32, 255, True)
        draw_rectangle(left, bottom, right, top, 255, 220, 100, 255, False)
        draw_centered_text(self.hud_font, UPGRADE_MODAL_TITLE_Y, "Upgrade?", (255, 220, 100))

        self._draw_upgrade_side(
            draw_rectangle,
            UPGRADE_MODAL_LEFT_RECT,
            "CURRENT",
            before_rows,
            set(),
        )
        self._draw_upgrade_side(
            draw_rectangle,
            UPGRADE_MODAL_RIGHT_RECT,
            "AFTER",
            after_rows,
            changed_indices,
        )
        draw_text_at(
            self.hud_font,
            SCREEN_WIDTH / 2,
            UPGRADE_MODAL_ARROW_Y,
            "->",
            (255, 220, 100),
        )
        draw_text_at(
            self.hud_font,
            SCREEN_WIDTH / 2,
            UPGRADE_MODAL_CHANCE_Y,
            "UPGRADE CHANCE {}%".format(chances.success),
            (255, 220, 100),
        )
        draw_text_at(
            self.hud_font,
            SCREEN_WIDTH / 2,
            UPGRADE_MODAL_CHANCE_DETAIL_Y,
            "SUCCESS {}%  FAIL {}%  DOWN {}%  DESTROY {}%".format(
                chances.success,
                chances.failure,
                chances.downgrade,
                chances.destroy,
            ),
        )

        for rect, label, hover_target, color in (
            (upgrade_confirm_rect(), "UPGRADE", ("upgrade_confirm",), (190, 140, 50)),
            (upgrade_cancel_rect(), "CANCEL", ("upgrade_cancel",), (120, 60, 55)),
        ):
            button_color = color if self.hover_target != hover_target else (220, 170, 60)
            draw_rectangle(
                rect[0],
                rect[1],
                rect[2],
                rect[3],
                *button_color,
                255,
                True,
            )
            draw_text_at(
                self.hud_font,
                (rect[0] + rect[2]) / 2,
                UPGRADE_MODAL_BUTTON_TEXT_Y,
                label,
            )

    def _play_buy_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            # Purchases are effects, so they follow the SFX volume.
            play_sound(BUY_GUN_SOUND_FILE)

    def _play_insufficient_funds_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            # Failed purchases/upgrades are effects, so they follow SFX volume.
            play_sound(BUY_UPGRADE_FAIL_SOUND_FILE)

    def _execute_action(self):
        if self.state is None or self.action_index == NO_ACTION:
            return
        if not self._action_available(self.gun_index, self.action_index):
            self._normalize_action()
            return
        gun_id = GUN_SHOP_ORDER[self.gun_index]
        if self.action_index == BUY_ACTION:
            self.last_result = purchase_gun(self.state, gun_id)
            if self.last_result.result is PurchaseResult.PURCHASED:
                self._play_buy_sound()
            elif self.last_result.result is PurchaseResult.INSUFFICIENT_COINS:
                self._play_insufficient_funds_sound()
            self._hide_state_panel()
            self._select_first_available_action()
        elif self.action_index == UPGRADE_ACTION:
            self._hide_state_panel()
            self.upgrade_modal_gun_id = gun_id
        else:
            return

    def _play_upgrade_sound(self, result):
        sound_file = UPGRADE_SOUND_BY_RESULT.get(result)
        if sound_file is None or self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            # Upgrade outcomes are effects, so they follow the SFX volume.
            play_sound(sound_file)

    def _confirm_upgrade(self):
        gun_id = self.upgrade_modal_gun_id
        if gun_id is None or self.state is None:
            return
        index = GUN_SHOP_ORDER.index(gun_id)
        if not self._action_available(index, UPGRADE_ACTION):
            self._hide_upgrade_modal()
            self._normalize_action()
            return
        self.gun_index = index
        self.action_index = UPGRADE_ACTION
        self.last_result = upgrade_gun(self.state, gun_id)
        self._play_upgrade_sound(self.last_result.result)
        if self.last_result.result is UpgradeResult.INSUFFICIENT_COINS:
            self._play_insufficient_funds_sound()
        self._hide_upgrade_modal()
        self._select_first_available_action()

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key == "escape":
            if self.upgrade_modal_gun_id is not None:
                self._hide_upgrade_modal()
            else:
                self.pending_action = "return_to_lobby"
        elif key == "space" and self.upgrade_modal_gun_id is not None:
            self._confirm_upgrade()

    def key_up(self, key):
        self.keys.discard(key.lower())

    def _target_at(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        if self.upgrade_modal_gun_id is not None:
            if contains(upgrade_confirm_rect(), screen_x, canvas_y):
                return ("upgrade_confirm",)
            if contains(upgrade_cancel_rect(), screen_x, canvas_y):
                return ("upgrade_cancel",)
            if contains(upgrade_modal_rect(), screen_x, canvas_y):
                return ("upgrade_modal",)
            return None
        if self.state_panel_gun_id is not None and contains(
            state_panel_rect(), screen_x, canvas_y
        ):
            return ("state_panel",)
        if contains(SHOP_EXIT_BUTTON, screen_x, canvas_y):
            return ("exit",)
        for index in range(len(GUN_SHOP_ORDER)):
            for action in (BUY_ACTION, UPGRADE_ACTION, STATE_ACTION):
                if not self._action_available(index, action):
                    continue
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
        if self.upgrade_modal_gun_id is not None:
            if target == ("upgrade_confirm",):
                self._confirm_upgrade()
            elif target == ("upgrade_cancel",):
                self._hide_upgrade_modal()
            else:
                self._hide_upgrade_modal()
            return
        if self.state_panel_gun_id is not None and target != ("state_panel",):
            self._hide_state_panel()
        if target is None or target[0] == "state_panel":
            return
        if target[0] == "exit":
            self.pending_action = "return_to_lobby"
        elif target[0] == "card":
            self.gun_index = target[1]
            self._select_first_available_action()
        elif target[0] == "button":
            self.gun_index = target[1]
            self.action_index = target[2]
            if target[2] == STATE_ACTION:
                self.state_panel_gun_id = GUN_SHOP_ORDER[target[1]]
                return
            self._execute_action()

    def mouse_up(self, button):
        return None

    def close(self):
        return None
