"""Training scene where the player can practise aiming and shooting."""

import math
import random

import pico2d

from game_config import (
    AIM_CURSOR_ALPHA,
    AIM_CURSOR_GAP,
    AIM_CURSOR_RADIUS,
    AIM_CURSOR_THICKNESS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from hud import draw_centered_text
from player import Player
from weapon import Gun


TRAINING_TITLE = "TRAINING"
TRAINING_NOTICE = "TRAINING GROUND OPENING SOON"
TRAINING_HINT = "PRESS SPACE : BACK TO LOBBY"
TRAINING_CURSOR_COLOR = (20, 20, 20)
TRAINING_CURSOR_ALPHA = AIM_CURSOR_ALPHA
TRAINING_TITLE_Y = SCREEN_HEIGHT - 200
TRAINING_NOTICE_Y = SCREEN_HEIGHT - 300
TRAINING_HINT_Y = 120


class TrainingTarget:
    """A simple circular target used in the training ground."""

    def __init__(self, x, y, radius=None, image=None):
        self.x = float(x)
        self.y = float(y)
        self.image = image
        if radius is None:
            if image is not None:
                radius = max(getattr(image, "w", 0), getattr(image, "h", 0)) / 2.0
            else:
                radius = 28.0
        self.radius = float(radius)
        self.hit_timer = 0.0

    def move_to(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.hit_timer = 0.0

    def update(self, delta_time):
        self.hit_timer = max(0.0, self.hit_timer - delta_time)

    def contains(self, x, y):
        return math.hypot(self.x - x, self.y - y) <= self.radius

    def draw(self, draw_rectangle):
        size = self.radius * 2.0
        if self.image is not None:
            try:
                self.image.draw(self.x, self.y, size, size)
                return
            except Exception:
                pass
        color = (255, 220, 80) if self.hit_timer > 0 else (220, 60, 60)
        try:
            pico2d.draw_circle(
                int(self.x),
                int(self.y),
                int(self.radius),
                *color,
                255,
                True,
            )
        except Exception:
            pass


class TrainingScene:
    """Training ground lifecycle: initialisation, update, and rendering."""

    def __init__(self, *args, **kwargs):
        state = kwargs.pop("state", None)
        hud_font = kwargs.pop("hud_font", None)
        random_source = kwargs.pop("random_source", None)
        player = kwargs.pop("player", None)
        gun = kwargs.pop("gun", None)
        background = kwargs.pop("background", None)
        target_image = kwargs.pop("target_image", None)

        for arg in args:
            if player is None and isinstance(arg, Player):
                player = arg
            elif gun is None and isinstance(arg, Gun):
                gun = arg
            elif state is None and hasattr(arg, "owned_guns"):
                state = arg
            elif hud_font is None and hasattr(arg, "draw") and hasattr(arg, "font"):
                hud_font = arg
            elif background is None and hasattr(arg, "draw") and not hasattr(arg, "font"):
                background = arg
            elif target_image is None and hasattr(arg, "draw") and hasattr(arg, "w"):
                target_image = arg

        if random_source is None:
            random_source = random.Random()

        self.state = state
        self.hud_font = hud_font
        self.random_source = random_source
        self.background = background
        self.target_image = target_image
        self.player = player if player is not None else Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.gun = gun if gun is not None else Gun()
        self.gun.infinite_ammo = True
        self.gun.heat_enabled = False
        self.target = TrainingTarget(SCREEN_WIDTH / 2 + 200, SCREEN_HEIGHT / 2 + 100, image=target_image)
        self._shots_fired = 0
        self._hits = 0
        self._misses = 0
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.mouse_held = False
        self._mouse_pressed = False
        self.exit_requested = False
        self.pending_action = None
        self.last_shot_result = None
        self.shot_result_timer = 0.0
        self.phase = "countdown"
        self.countdown_remaining = 3.0
        self.time_remaining = 60.0
        self.finish_timer = 2.0

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

        self.shot_result_timer = max(0.0, self.shot_result_timer - delta_time)

        if self.phase == "countdown":
            self.countdown_remaining = max(0.0, self.countdown_remaining - delta_time)
            if self.countdown_remaining <= 0.0:
                self.phase = "playing"
                self.time_remaining = 60.0
            return

        if self.phase == "finished":
            self.finish_timer = max(0.0, self.finish_timer - delta_time)
            if self.finish_timer <= 0.0:
                self.pending_action = "return_to_lobby"
            return

        # playing
        self.time_remaining = max(0.0, self.time_remaining - delta_time)
        self.gun.update(delta_time)
        fired = self.gun.handle_fire_input(
            mouse_held=self.mouse_held,
            mouse_pressed=self._mouse_pressed,
        )
        self._mouse_pressed = False
        if fired:
            self._shots_fired += 1
            if self._shot_hits_target(canvas_x, canvas_y):
                self._hits += 1
                if self.target is not None:
                    self.target.hit_timer = 0.3
                    self._respawn_target()
                self.last_shot_result = "HIT"
            else:
                self._misses += 1
                self.last_shot_result = "MISS"
            self.shot_result_timer = 0.6

        if self.time_remaining <= 0.0:
            self.phase = "finished"
            self.finish_timer = 2.0

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
                16,
                26,
                16,
                255,
                True,
            )
        if self.target is not None:
            self.target.draw(draw_rectangle)
        if self.player is not None and self.player.image is not None:
            self.player.draw()
        self._draw_aim_cursor(draw_rectangle)
        if self.hud_font is None:
            return
        draw_centered_text(
            self.hud_font,
            TRAINING_TITLE_Y,
            TRAINING_TITLE,
            (0, 120, 0),
        )

        if self.phase == "countdown":
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT * 3/ 4,
                str(int(self.countdown_remaining) + 1) if self.countdown_remaining > 0 else "START",
                (0, 0, 0),
            )
        elif self.phase == "finished":
            pico2d.draw_rectangle (
                SCREEN_WIDTH / 2 - 200,
                SCREEN_HEIGHT / 2 - 100,
                SCREEN_WIDTH / 2 + 200,
                SCREEN_HEIGHT / 2 + 100,
                0,
                20,
                40,
                255,
                True
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT / 2 + 40,
                "TIME UP",
                (222, 180, 0),
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT / 2 - 40,
                "HITS {}".format(self._hits),
                (255, 255, 255),
            )
        else:
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT - 80,
                "TIME {:02d}".format(int(self.time_remaining)),
                (255, 255, 255),
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT - 130,
                "HITS {}".format(self._hits),
                (120, 20, 0),
            )

    @property
    def aim_cursor_position(self):
        return self.mouse_screen_x, SCREEN_HEIGHT - self.mouse_screen_y

    def _draw_aim_cursor(self, draw_rectangle):
        cursor_x, cursor_y = self.aim_cursor_position
        radius = AIM_CURSOR_RADIUS
        gap = AIM_CURSOR_GAP
        half = AIM_CURSOR_THICKNESS / 2.0
        segments = (
            (cursor_x - radius, cursor_y - half, cursor_x - gap, cursor_y + half),
            (cursor_x + gap, cursor_y - half, cursor_x + radius, cursor_y + half),
            (cursor_x - half, cursor_y - radius, cursor_x + half, cursor_y - gap),
            (cursor_x - half, cursor_y + gap, cursor_x + half, cursor_y + radius),
        )
        for x1, y1, x2, y2 in segments:
            draw_rectangle(
                x1,
                y1,
                x2,
                y2,
                TRAINING_CURSOR_COLOR[0],
                TRAINING_CURSOR_COLOR[1],
                TRAINING_CURSOR_COLOR[2],
                TRAINING_CURSOR_ALPHA,
                True,
            )
        draw_rectangle(
            cursor_x - half,
            cursor_y - half,
            cursor_x + half,
            cursor_y + half,
            TRAINING_CURSOR_COLOR[0],
            TRAINING_CURSOR_COLOR[1],
            TRAINING_CURSOR_COLOR[2],
            TRAINING_CURSOR_ALPHA,
            True,
        )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key == "e":
            self.gun.toggle_mode()
        elif key == "r":
            self.gun.start_reload()
        elif key in ("escape", "q"):
            self.pending_action = "return_to_lobby"

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y

    def _respawn_target(self):
        margin = 80.0
        self.target.move_to(
            self.random_source.uniform(margin, SCREEN_WIDTH - margin),
            self.random_source.uniform(margin, SCREEN_HEIGHT - margin),
        )

    @property
    def accuracy(self):
        if self._shots_fired <= 0:
            return 0.0
        return self._hits / self._shots_fired

    @property
    def hit_rate(self):
        return self.accuracy

    @property
    def misses(self):
        return self._misses

    @property
    def miss_count(self):
        return self._misses

    @property
    def hits(self):
        return self._hits

    @property
    def hit_count(self):
        return self._hits

    @property
    def shots(self):
        return self._shots_fired

    @property
    def shots_fired(self):
        return self._shots_fired

    def _shot_hits_target(self, aim_x, aim_y):
        """Return whether the given aim point hits the current target."""
        if self.target is None:
            return False
        return self.target.contains(aim_x, aim_y)

    def mouse_down(self, button, screen_x=None, screen_y=None):
        return None

    def mouse_up(self, button):
        return None

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if button == "left":
            self.mouse_held = True
            self._mouse_pressed = True
            if screen_x is not None and screen_y is not None:
                self.mouse_screen_x = screen_x
                self.mouse_screen_y = screen_y

    def mouse_up(self, button):
        if button == "left":
            self.mouse_held = False

    def close(self):
        return None
