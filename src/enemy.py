"""Shared state and lifecycle for enemy entities."""

from dataclasses import dataclass
from enum import Enum

from game_config import FPS


ENEMY_DEFAULT_MOVE_SPEED = 60.0
ENEMY_DEFAULT_RADIUS = 16.0


class EnemyType(Enum):
    BASIC = "basic"
    EXPLOSIVE = "explosive"
    TANKER = "tanker"
    ASSASSIN = "assassin"
    ARCHER = "archer"


@dataclass(frozen=True)
class EnemyStats:
    name: str
    max_hp: float
    attack_damage: float
    attack_interval: float
    move_speed: float
    radius: float = 16.0
    attack_range: float = 0.0


ENEMY_STATS = {
    EnemyType.BASIC: EnemyStats(
        "basic", 20, 8, 0.8, ENEMY_DEFAULT_MOVE_SPEED, ENEMY_DEFAULT_RADIUS
    ),
    EnemyType.EXPLOSIVE: EnemyStats(
        "explosive",
        80,
        15,
        1.5,
        ENEMY_DEFAULT_MOVE_SPEED,
        ENEMY_DEFAULT_RADIUS,
        attack_range=20,
    ),
    EnemyType.TANKER: EnemyStats(
        "tanker", 120, 5, 2.0, ENEMY_DEFAULT_MOVE_SPEED, ENEMY_DEFAULT_RADIUS
    ),
    EnemyType.ASSASSIN: EnemyStats(
        "assassin", 10, 10, 0.5, ENEMY_DEFAULT_MOVE_SPEED, ENEMY_DEFAULT_RADIUS
    ),
    EnemyType.ARCHER: EnemyStats(
        "archer",
        50,
        10,
        1.2,
        ENEMY_DEFAULT_MOVE_SPEED,
        ENEMY_DEFAULT_RADIUS,
        attack_range=150,
    ),
}


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
        self._movement_per_frame = self.move_speed / FPS

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
        if self.player is None or not self.is_alive:
            return
        direction_x = self.player.x - self.x
        direction_y = self.player.y - self.y
        distance = (direction_x**2 + direction_y**2) ** 0.5
        contact_distance = self.radius + self.player.radius
        if distance <= contact_distance or distance == 0:
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            return
        self.velocity_x = direction_x / distance
        self.velocity_y = direction_y / distance
        travel_distance = min(self._movement_per_frame, distance - contact_distance)
        self.x += self.velocity_x * travel_distance
        self.y += self.velocity_y * travel_distance

    def draw(self):
        if self.image is None:
            raise RuntimeError("Enemy.draw requires a loaded enemy image")
        x, y = self._screen_position or (self.x, self.y)
        self.image.draw(x, y, self.radius * 2, self.radius * 2)
