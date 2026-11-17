"""Training scene where the player can practise aiming and shooting."""

import math

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_centered_text
from player import Player


TRAINING_TITLE = "TRAINING"
TRAINING_NOTICE = "TRAINING GROUND OPENING SOON"
TRAINING_HINT = "PRESS SPACE : BACK TO LOBBY"
TRAINING_TITLE_Y = SCREEN_HEIGHT - 200
TRAINING_NOTICE_Y = SCREEN_HEIGHT - 300
TRAINING_HINT_Y = 120


class TrainingTarget:
    """A simple circular target used in the training ground."""

    def __init__(self, x, y, radius=28.0):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.hit_timer = 0.0

    def update(self, delta_time):
        self.hit_timer = max(0.0, self.hit_timer - delta_time)

    def draw(self, draw_rectangle):
        radius = self.radius
        if self.hit_timer > 0:
            color = (255, 220, 80)
        else:
            color = (220, 60, 60)
        draw_rectangle(
            self.x - radius,
            self.y - radius,
            self.x + radius,
            self.y + radius,
            *color,
            255,
            True,
        )


class TrainingScene:
    """Training ground lifecycle: initialisation, update, and rendering."""

    def __init__(self, *args, **kwargs):
        self.state = kwargs.pop("state", None)
        self.hud_font = kwargs.pop("hud_font", None)
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.target = TrainingTarget(SCREEN_WIDTH / 2 + 200, SCREEN_HEIGHT / 2 + 100)
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.exit_requested = False
        self.pending_action = None

    def update(self, delta_time):
        canvas_x = self.mouse_screen_x
        canvas_y = SCREEN_HEIGHT - self.mouse_screen_y
        if self.player is not None:
            self.player.aim_at(canvas_x, canvas_y)
            self.player.x = SCREEN_WIDTH / 2
            self.player.y = SCREEN_HEIGHT / 2
            self.player.set_movement(0, 0)
        if self.target is not None:
            self.target.update(delta_time)

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
        if self.target is not None:
            self.target.draw(draw_rectangle)
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

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y

    def _shot_hits_target(self, aim_x, aim_y):
        """Return whether the given aim point hits the current target."""
        if self.target is None:
            return False
        return self.target.contains(aim_x, aim_y)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        return None

    def mouse_up(self, button):
        return None

    def close(self):
        return None
