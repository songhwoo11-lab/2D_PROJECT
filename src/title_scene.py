"""Title screen with the main menu buttons."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_centered_text, draw_text_at_center


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

RESET_BUTTON_INDEX = tuple(action for _, action in TITLE_ACTIONS).index(
    RESET_GAME_ACTION
)
RESET_DIALOG_TITLE = "Do Reset Game?"
RESET_COMPLETE_TITLE = "Reset Complete!"
RESET_COMPLETE_SECONDS = 1.5

RESET_DIALOG_WIDTH = 620
RESET_DIALOG_HEIGHT = 360
RESET_DIALOG_LEFT = (SCREEN_WIDTH - RESET_DIALOG_WIDTH) // 2
RESET_DIALOG_BOTTOM = (SCREEN_HEIGHT - RESET_DIALOG_HEIGHT) // 2
RESET_DIALOG_RIGHT = RESET_DIALOG_LEFT + RESET_DIALOG_WIDTH
RESET_DIALOG_TOP = RESET_DIALOG_BOTTOM + RESET_DIALOG_HEIGHT
RESET_DIALOG_TITLE_Y = RESET_DIALOG_TOP - 90
RESET_DIALOG_BUTTON_WIDTH = 180
RESET_DIALOG_BUTTON_HEIGHT = 80
RESET_DIALOG_BUTTON_BOTTOM = RESET_DIALOG_BOTTOM + 70
RESET_DIALOG_BUTTON_GAP = 60
RESET_DIALOG_BUTTONS_WIDTH = (
    RESET_DIALOG_BUTTON_WIDTH * 2 + RESET_DIALOG_BUTTON_GAP
)
RESET_DIALOG_YES_RECT = (
    RESET_DIALOG_LEFT
    + (RESET_DIALOG_WIDTH - RESET_DIALOG_BUTTONS_WIDTH) // 2,
    RESET_DIALOG_BUTTON_BOTTOM,
    RESET_DIALOG_LEFT
    + (RESET_DIALOG_WIDTH - RESET_DIALOG_BUTTONS_WIDTH) // 2
    + RESET_DIALOG_BUTTON_WIDTH,
    RESET_DIALOG_BUTTON_BOTTOM + RESET_DIALOG_BUTTON_HEIGHT,
)
RESET_DIALOG_NO_RECT = (
    RESET_DIALOG_YES_RECT[2] + RESET_DIALOG_BUTTON_GAP,
    RESET_DIALOG_BUTTON_BOTTOM,
    RESET_DIALOG_YES_RECT[2] + RESET_DIALOG_BUTTON_GAP + RESET_DIALOG_BUTTON_WIDTH,
    RESET_DIALOG_BUTTON_BOTTOM + RESET_DIALOG_BUTTON_HEIGHT,
)
RESET_DIALOG_BUTTON_TEXT_Y = RESET_DIALOG_BUTTON_BOTTOM + RESET_DIALOG_BUTTON_HEIGHT // 2
RESET_DIALOG_PANEL_COLOR = (30, 42, 38, 255)
RESET_DIALOG_YES_COLOR = (150, 60, 55, 255)
RESET_DIALOG_NO_COLOR = (60, 100, 150, 255)
RESET_DIALOG_TEXT_COLOR = (255, 255, 255)


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
        self.mode = "menu"
        self.reset_complete_remaining = 0.0

    def update(self, delta_time):
        if self.mode != "complete":
            return None
        self.reset_complete_remaining = max(
            0.0, self.reset_complete_remaining - delta_time
        )
        if self.reset_complete_remaining == 0.0:
            self.mode = "menu"
        return None

    def show_reset_complete(self):
        """Show the completion message before returning to the menu."""
        self.mode = "complete"
        self.reset_complete_remaining = RESET_COMPLETE_SECONDS

    def _draw_background(self, draw_rectangle):
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

    def _draw_dialog_base(self, draw_rectangle, title):
        # Keep the title background and logo visible behind the dialog.
        draw_rectangle(
            RESET_DIALOG_LEFT,
            RESET_DIALOG_BOTTOM,
            RESET_DIALOG_RIGHT,
            RESET_DIALOG_TOP,
            *RESET_DIALOG_PANEL_COLOR,
            True,
        )
        if self.hud_font is not None:
            draw_centered_text(
                self.hud_font,
                RESET_DIALOG_TITLE_Y,
                title,
                RESET_DIALOG_TEXT_COLOR,
            )

    def _draw_reset_confirmation(self, draw_rectangle):
        self._draw_dialog_base(draw_rectangle, RESET_DIALOG_TITLE)
        draw_rectangle(*RESET_DIALOG_YES_RECT, *RESET_DIALOG_YES_COLOR, True)
        draw_rectangle(*RESET_DIALOG_NO_RECT, *RESET_DIALOG_NO_COLOR, True)
        if self.hud_font is not None:
            for rect, label in (
                (RESET_DIALOG_YES_RECT, "YES"),
                (RESET_DIALOG_NO_RECT, "NO"),
            ):
                draw_text_at_center(
                    self.hud_font,
                    (rect[0] + rect[2]) / 2,
                    RESET_DIALOG_BUTTON_TEXT_Y,
                    label,
                    RESET_DIALOG_TEXT_COLOR,
                )

    def _draw_reset_complete(self, draw_rectangle):
        self._draw_dialog_base(draw_rectangle, RESET_COMPLETE_TITLE)

    def _draw_menu_buttons(self, draw_rectangle):
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

    def draw(self, draw_rectangle):
        self._draw_background(draw_rectangle)
        # The menu buttons stay on the title background in every mode; the
        # confirmation/completion panel is drawn on top of them.
        self._draw_menu_buttons(draw_rectangle)
        if self.mode == "confirm":
            self._draw_reset_confirmation(draw_rectangle)
        elif self.mode == "complete":
            self._draw_reset_complete(draw_rectangle)

    def _index_at(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        for index in range(len(TITLE_ACTIONS)):
            if contains(button_rect(index), screen_x, canvas_y):
                return index
        return None

    def _reset_dialog_target(self, screen_x, screen_y):
        canvas_y = SCREEN_HEIGHT - screen_y
        if contains(RESET_DIALOG_YES_RECT, screen_x, canvas_y):
            return "yes"
        if contains(RESET_DIALOG_NO_RECT, screen_x, canvas_y):
            return "no"
        return None

    def _activate(self, index):
        if index is None:
            return
        self.hover_index = index
        if index == RESET_BUTTON_INDEX:
            self.mode = "confirm"
            return
        self.pending_action = TITLE_ACTIONS[index][1]

    def mouse_move(self, screen_x, screen_y):
        if self.mode != "menu":
            return
        self.hover_index = self._index_at(screen_x, screen_y)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if button != "left" or screen_x is None or screen_y is None:
            return
        if self.mode == "confirm":
            target = self._reset_dialog_target(screen_x, screen_y)
            if target == "yes":
                self.pending_action = RESET_GAME_ACTION
            elif target == "no":
                self.mode = "menu"
            return
        if self.mode == "complete":
            self.mode = "menu"
            return
        self._activate(self._index_at(screen_x, screen_y))

    def mouse_up(self, button):
        return None

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.mode == "confirm":
            if key in ("escape", "right"):
                self.mode = "menu"
            elif key in ("space", "return", "e", "left"):
                self.pending_action = RESET_GAME_ACTION
            return
        if self.mode == "complete":
            if key in ("escape", "space", "return", "e"):
                self.mode = "menu"
            return
        if key in ("up", "w", "down", "s"):
            current = self.hover_index if self.hover_index is not None else 0
            step = -1 if key in ("up", "w") else 1
            self.hover_index = (current + step) % len(TITLE_ACTIONS)
        elif key in ("space", "return", "e"):
            self._activate(self.hover_index)

    def key_up(self, key):
        self.keys.discard(key.lower())

    def close(self):
        return None
