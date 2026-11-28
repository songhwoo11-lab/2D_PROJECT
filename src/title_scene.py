"""Title screen with the main menu buttons."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_text_at_center


GAME_START_ACTION = "game_start"
SETTINGS_ACTION = "title_settings"
RESET_GAME_ACTION = "reset_game"
EXIT_GAME_ACTION = "exit_game"

TITLE_ACTIONS = (
    ("Game Start", GAME_START_ACTION),
    ("Setting", SETTINGS_ACTION),
    ("Reset Game", RESET_GAME_ACTION),
    ("Exit Game", EXIT_GAME_ACTION),
)

TITLE_BACKGROUND_COLOR = (18, 26, 22, 255)
TITLE_LOGO_WIDTH = 768
TITLE_LOGO_HEIGHT = 576
TITLE_LOGO_TOP_MARGIN = 40

TITLE_BUTTON_WIDTH = 360
TITLE_BUTTON_HEIGHT = 78
TITLE_BUTTON_GAP = 28
TITLE_BUTTON_TOTAL_HEIGHT = (
    len(TITLE_ACTIONS) * TITLE_BUTTON_HEIGHT
    + (len(TITLE_ACTIONS) - 1) * TITLE_BUTTON_GAP
)
TITLE_BUTTON_TOP_GAP = 40
TITLE_BUTTON_FIRST_TOP = (
    SCREEN_HEIGHT - TITLE_LOGO_TOP_MARGIN - TITLE_LOGO_HEIGHT - TITLE_BUTTON_TOP_GAP
)
TITLE_BUTTON_CENTER_Y = TITLE_BUTTON_FIRST_TOP - TITLE_BUTTON_TOTAL_HEIGHT / 2
TITLE_BUTTON_COLOR = (45, 80, 105, 255)
TITLE_BUTTON_HOVER_COLOR = (70, 120, 150, 255)
TITLE_BUTTON_TEXT_COLOR = (255, 255, 255)


def button_rect(index):
    """Return a menu button rectangle in canvas coordinates."""
    left = (SCREEN_WIDTH - TITLE_BUTTON_WIDTH) / 2
    top = TITLE_BUTTON_FIRST_TOP - index * (TITLE_BUTTON_HEIGHT + TITLE_BUTTON_GAP)
    bottom = top - TITLE_BUTTON_HEIGHT
    return left, bottom, left + TITLE_BUTTON_WIDTH, top


def logo_center():
    """Return the canvas center position of the logo near the top edge."""
    return (
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT - TITLE_LOGO_TOP_MARGIN - TITLE_LOGO_HEIGHT / 2,
    )


def contains(rect, x, y):
    if x is None or y is None:
        return False
    left, bottom, right, top = rect
    return left <= x <= right and bottom <= y <= top


class TitleScene:
    """Menu that opens before the lobby without playing any audio."""

    def __init__(self, background=None, logo=None, hud_font=None):
        self.background = background
        self.logo = logo
        self.hud_font = hud_font
        self.keys = set()
        self.hover_index = 0
        self.pending_action = None
        self.exit_requested = False

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
                *TITLE_BACKGROUND_COLOR,
                True,
            )
        if self.logo is not None:
            x, y = logo_center()
            self.logo.draw(x, y, TITLE_LOGO_WIDTH, TITLE_LOGO_HEIGHT)
        if self.hud_font is None:
            return
        for index, (label, _) in enumerate(TITLE_ACTIONS):
            rect = button_rect(index)
            color = (
                TITLE_BUTTON_HOVER_COLOR
                if index == self.hover_index
                else TITLE_BUTTON_COLOR
            )
            draw_rectangle(*rect, *color, True)
            draw_text_at_center(
                self.hud_font,
                (rect[0] + rect[2]) / 2,
                (rect[1] + rect[3]) / 2,
                label,
                TITLE_BUTTON_TEXT_COLOR,
            )

    def _index_at(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        for index in range(len(TITLE_ACTIONS)):
            if contains(button_rect(index), screen_x, canvas_y):
                return index
        return None

    def _activate(self, index):
        if index is None:
            return
        self.hover_index = index
        self.pending_action = TITLE_ACTIONS[index][1]

    def mouse_move(self, screen_x, screen_y):
        self.hover_index = self._index_at(screen_x, screen_y)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if button != "left" or screen_x is None or screen_y is None:
            return
        self._activate(self._index_at(screen_x, screen_y))

    def mouse_up(self, button):
        return None

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key in ("up", "w"):
            self.hover_index = (self.hover_index - 1) % len(TITLE_ACTIONS)
        elif key in ("down", "s"):
            self.hover_index = (self.hover_index + 1) % len(TITLE_ACTIONS)
        elif key in ("space", "return", "e"):
            self._activate(self.hover_index)

    def key_up(self, key):
        self.keys.discard(key.lower())

    def close(self):
        return None
