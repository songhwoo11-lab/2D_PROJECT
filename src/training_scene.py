"""Training scene where the player can practise aiming and shooting."""

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_centered_text
from player import Player


TRAINING_TITLE = "TRAINING"
TRAINING_NOTICE = "TRAINING GROUND OPENING SOON"
TRAINING_HINT = "PRESS SPACE : BACK TO LOBBY"
TRAINING_TITLE_Y = SCREEN_HEIGHT - 200
TRAINING_NOTICE_Y = SCREEN_HEIGHT - 300
TRAINING_HINT_Y = 120


class TrainingScene:
    """Training ground lifecycle: initialisation, update, and rendering."""

    def __init__(self, *args, **kwargs):
        self.state = kwargs.pop("state", None)
        self.hud_font = kwargs.pop("hud_font", None)
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
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
            16,
            26,
            16,
            255,
            True,
        )
        if self.hud_font is None:
            return
        if self.player is not None and self.player.image is not None:
            self.player.draw()
        draw_centered_text(
            self.hud_font,
            TRAINING_TITLE_Y,
            TRAINING_TITLE,
            (255, 220, 100),
        )
        draw_centered_text(self.hud_font, TRAINING_NOTICE_Y, TRAINING_NOTICE)
        draw_centered_text(
            self.hud_font,
            TRAINING_HINT_Y,
            TRAINING_HINT,
            (170, 190, 220),
        )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key in ("space", "q"):
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
