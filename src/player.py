"""Player state and rendering for the first playable battle stage."""

import math

from game_config import (
    PLAYER_MAX_HP,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from hp_trail import HpTrail


class Player:
    def __init__(
        self,
        x,
        y,
        image=None,
        max_hp=PLAYER_MAX_HP,
        speed=PLAYER_SPEED,
        radius=PLAYER_RADIUS,
    ):
        if max_hp <= 0:
            raise ValueError("max_hp must be positive")
        self.x = float(x)
        self.y = float(y)
        self.image = image
        self.max_hp = int(max_hp)
        self.hp = self.max_hp
        self.hp_trail = HpTrail(self.hp, self.max_hp)
        self.speed = float(speed)
        self.radius = float(radius)
        self.aim_angle = 0.0
        self._move_x = 0.0
        self._move_y = 0.0
        self._delta_time = 0.0
        self._screen_position = None

    @property
    def is_alive(self):
        return self.hp > 0

    @property
    def is_defeated(self):
        return not self.is_alive

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("damage must be non-negative")
        self.hp = max(0, self.hp - amount)
        return self.is_defeated

    def heal(self, amount):
        if amount < 0:
            raise ValueError("heal amount must be non-negative")
        previous_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - previous_hp

    def update_hp_trail(self, delta_time):
        self.hp_trail.update(self.hp, delta_time)

    def reset_hp_trail(self):
        self.hp_trail.reset(self.hp, self.max_hp)

    def set_movement(self, move_x, move_y, delta_time):
        if not math.isfinite(delta_time) or delta_time < 0:
            raise ValueError("delta_time must be a finite non-negative number")
        self._move_x = float(move_x)
        self._move_y = float(move_y)
        self._delta_time = float(delta_time)

    def aim_at(self, world_x, world_y):
        direction_x = world_x - self.x
        direction_y = world_y - self.y
        if direction_x == 0 and direction_y == 0:
            return self.aim_angle
        self.aim_angle = math.atan2(direction_y, direction_x)
        return self.aim_angle

    def set_screen_position(self, screen_x, screen_y):
        self._screen_position = (screen_x, screen_y)

    @property
    def screen_position(self):
        if self._screen_position is None:
            return self.x, self.y
        return self._screen_position

    def update(self):
        direction_length = math.hypot(self._move_x, self._move_y)
        if direction_length > 1:
            move_x = self._move_x / direction_length
            move_y = self._move_y / direction_length
        else:
            move_x = self._move_x
            move_y = self._move_y
        self.x += move_x * self.speed * self._delta_time
        self.y += move_y * self.speed * self._delta_time
        self.x = min(max(self.x, self.radius), WORLD_WIDTH - self.radius)
        self.y = min(max(self.y, self.radius), WORLD_HEIGHT - self.radius)

    def draw(self, screen_x=None, screen_y=None):
        if self.image is None:
            raise RuntimeError("Player.draw requires a loaded player image")
        if screen_x is None and self._screen_position is not None:
            x, y = self.screen_position
        else:
            x = self.x if screen_x is None else screen_x
            y = self.y if screen_y is None else screen_y
        self.image.draw(x, y, self.radius * 2, self.radius * 2)
