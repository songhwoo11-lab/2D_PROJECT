"""Visual arrow projectile fired by an archer enemy."""

import math

import game_world
from game_config import (
    ARROW_HIT_RADIUS,
    ARROW_SIZE,
    ARROW_SPEED,
    FPS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)


class Arrow:
    SPRITE_DIRECTION_OFFSET = 3 * math.pi / 4

    def __init__(
        self,
        x,
        y,
        target_x,
        target_y,
        image,
        speed=ARROW_SPEED,
        target=None,
        damage=0,
        max_distance=None,
    ):
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.image = image
        self.speed = float(speed)
        self.radius = ARROW_HIT_RADIUS
        self.target = target
        self.damage = damage
        self.max_distance = max_distance
        self.distance_travelled = 0.0
        self.angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
        self._screen_position = None

    def set_screen_position(self, screen_x, screen_y):
        self._screen_position = (screen_x, screen_y)

    def update(self):
        previous_x = self.x
        previous_y = self.y
        if self.max_distance is not None:
            remaining_range = self.max_distance - self.distance_travelled
            if remaining_range <= 0:
                game_world.remove_object(self)
                return
            travel_distance = min(self.speed / FPS, remaining_range)
            direction_x = math.cos(self.angle)
            direction_y = math.sin(self.angle)
        else:
            direction_x = self.target_x - self.x
            direction_y = self.target_y - self.y
            distance = math.hypot(direction_x, direction_y)
            if distance == 0:
                game_world.remove_object(self)
                return
            travel_distance = min(self.speed / FPS, distance)
            direction_x /= distance
            direction_y /= distance

        self.x += direction_x * travel_distance
        self.y += direction_y * travel_distance
        self.distance_travelled += travel_distance
        if self._hits_target(previous_x, previous_y):
            self.target.take_damage(self.damage)
            game_world.remove_object(self)
            return
        if not (0 <= self.x <= WORLD_WIDTH and 0 <= self.y <= WORLD_HEIGHT):
            game_world.remove_object(self)
            return
        if self.max_distance is not None:
            if self.distance_travelled >= self.max_distance:
                game_world.remove_object(self)
        elif travel_distance >= distance:
            game_world.remove_object(self)

    def _hits_target(self, start_x, start_y):
        if self.target is None:
            return False
        segment_x = self.x - start_x
        segment_y = self.y - start_y
        segment_length_squared = segment_x * segment_x + segment_y * segment_y
        if segment_length_squared == 0:
            closest_x = start_x
            closest_y = start_y
        else:
            projection = (
                (self.target.x - start_x) * segment_x
                + (self.target.y - start_y) * segment_y
            ) / segment_length_squared
            projection = min(1.0, max(0.0, projection))
            closest_x = start_x + projection * segment_x
            closest_y = start_y + projection * segment_y
        return math.hypot(
            self.target.x - closest_x,
            self.target.y - closest_y,
        ) <= self.target.radius + self.radius

    def draw(self):
        if self.image is None:
            raise RuntimeError("Arrow.draw requires a loaded arrow image")
        x, y = self._screen_position or (self.x, self.y)
        self.image.rotate_draw(
            self.angle - self.SPRITE_DIRECTION_OFFSET,
            x,
            y,
            ARROW_SIZE,
            ARROW_SIZE,
        )
