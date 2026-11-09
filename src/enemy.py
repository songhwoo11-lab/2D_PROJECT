"""Shared state and lifecycle for enemy entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnemyStats:
    name: str
    max_hp: float
    attack_damage: float
    attack_interval: float
    move_speed: float
    radius: float = 16.0
    attack_range: float = 0.0


class Enemy:
    def __init__(self, x, y, stats, image=None, player=None):
        if stats.max_hp <= 0:
            raise ValueError("enemy max_hp must be positive")
        if stats.attack_interval <= 0:
            raise ValueError("enemy attack_interval must be positive")
        if stats.radius <= 0:
            raise ValueError("enemy radius must be positive")
        self.x = float(x)
        self.y = float(y)
        self.stats = stats
        self.max_hp = float(stats.max_hp)
        self.hp = self.max_hp
        self.attack_damage = float(stats.attack_damage)
        self.attack_interval = float(stats.attack_interval)
        self.move_speed = float(stats.move_speed)
        self.radius = float(stats.radius)
        self.player = player
        self.image = image
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self._screen_position = None

    @property
    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("damage must be non-negative")
        self.hp = max(0.0, self.hp - amount)
        return not self.is_alive

    def set_screen_position(self, screen_x, screen_y):
        self._screen_position = (screen_x, screen_y)

    def update(self):
        pass

    def draw(self):
        if self.image is None:
            raise RuntimeError("Enemy.draw requires a loaded enemy image")
        x, y = self._screen_position or (self.x, self.y)
        self.image.draw(x, y, self.radius * 2, self.radius * 2)
