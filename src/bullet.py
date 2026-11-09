"""Projectile visuals and movement for player shots."""

import math

import game_world
from game_config import BULLET_SIZE, BULLET_SPEED, FPS, WORLD_HEIGHT, WORLD_WIDTH
from enemy import Enemy


class Bullet:
    def __init__(self, x, y, angle, image, speed=BULLET_SPEED):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.image = image
        self.speed = float(speed)
        self.radius = BULLET_SIZE / 2
        self.hit_target = None
        self._screen_position = None

    def set_screen_position(self, screen_x, screen_y):
        self._screen_position = (screen_x, screen_y)

    def update(self):
        distance = self.speed / FPS
        self.x += math.cos(self.angle) * distance
        self.y += math.sin(self.angle) * distance
        for layer in tuple(game_world.world):
            for obj in tuple(layer):
                if isinstance(obj, Enemy) and self.collides_with(obj):
                    self.hit_target = obj
                    game_world.remove_object(self)
                    return
        if not (0 <= self.x <= WORLD_WIDTH and 0 <= self.y <= WORLD_HEIGHT):
            game_world.remove_object(self)

    def collides_with(self, enemy):
        return math.hypot(enemy.x - self.x, enemy.y - self.y) <= (
            enemy.radius + self.radius
        )

    def draw(self):
        if self.image is None:
            raise RuntimeError("Bullet.draw requires a loaded bullet image")
        x, y = self._screen_position or (self.x, self.y)
        self.image.rotate_draw(
            self.angle - math.pi / 4,
            x,
            y,
            BULLET_SIZE,
            BULLET_SIZE,
        )
