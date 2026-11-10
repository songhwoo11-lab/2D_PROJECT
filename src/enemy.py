"""Shared state and lifecycle for enemy entities."""

from dataclasses import dataclass
from enum import Enum
import math

import game_world
from game_config import DISTANCE_EPSILON, FPS


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
        ENEMY_DEFAULT_MOVE_SPEED * 1.8,
        ENEMY_DEFAULT_RADIUS,
        attack_range=50,
    ),
    EnemyType.TANKER: EnemyStats(
        "tanker", 120, 5, 2.0, ENEMY_DEFAULT_MOVE_SPEED, ENEMY_DEFAULT_RADIUS
    ),
    EnemyType.ASSASSIN: EnemyStats(
        "assassin",
        10,
        10,
        0.5,
        ENEMY_DEFAULT_MOVE_SPEED * 2,
        ENEMY_DEFAULT_RADIUS,
    ),
    EnemyType.ARCHER: EnemyStats(
        "archer",
        50,
        10,
        1.2,
        ENEMY_DEFAULT_MOVE_SPEED,
        ENEMY_DEFAULT_RADIUS,
        attack_range=300,
    ),
}


class Enemy:
    def __init__(self, x, y, stats, image=None, player=None, draw_rectangle=None):
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
        self.draw_rectangle = draw_rectangle
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self._screen_position = None
        self._movement_per_frame = self.move_speed / FPS
        self._attack_cooldown_frames = 0.0
        self._uses_spatial_collision = True

    @property
    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("damage must be non-negative")
        self.hp = max(0.0, self.hp - amount)
        return not self.is_alive

    def collides_with(self, other):
        distance = math.hypot(other.x - self.x, other.y - self.y)
        return distance <= self.radius + other.radius

    def move_towards(self, target_x, target_y, max_distance):
        direction_x = target_x - self.x
        direction_y = target_y - self.y
        distance = math.hypot(direction_x, direction_y)
        if max_distance <= 0:
            return False

        enemies = game_world.nearby_spatial_objects(
            self,
            max_distance + self.radius,
        )
        if distance == 0 and not enemies:
            return False

        base_angle = math.atan2(direction_y, direction_x) if distance else 0.0
        angle_offsets = [0.0]
        for degrees in range(15, 180, 15):
            angle_offsets.extend(
                (math.radians(degrees), -math.radians(degrees))
            )
        angle_offsets.append(math.pi)

        best_position = None
        best_score = None
        for angle_offset in angle_offsets:
            angle = base_angle + angle_offset
            next_x = self.x + math.cos(angle) * max_distance
            next_y = self.y + math.sin(angle) * max_distance
            overlap_improvement = 0.0
            is_clear = True
            for other in enemies:
                minimum_distance = self.radius + other.radius
                current_distance = math.hypot(other.x - self.x, other.y - self.y)
                segment_distance = self._distance_to_segment(
                    other.x,
                    other.y,
                    self.x,
                    self.y,
                    next_x,
                    next_y,
                )
                next_distance = math.hypot(other.x - next_x, other.y - next_y)
                if current_distance < minimum_distance - DISTANCE_EPSILON:
                    if (
                        segment_distance + DISTANCE_EPSILON < current_distance
                        or next_distance <= current_distance + DISTANCE_EPSILON
                    ):
                        is_clear = False
                        break
                    overlap_improvement += next_distance - current_distance
                elif segment_distance + DISTANCE_EPSILON < minimum_distance:
                    is_clear = False
                    break

            if not is_clear:
                continue
            if angle_offset == 0:
                self.x = next_x
                self.y = next_y
                game_world.refresh_spatial_position(self)
                return True
            remaining_distance = math.hypot(
                target_x - next_x,
                target_y - next_y,
            )
            progress = distance - remaining_distance
            score = (overlap_improvement, progress)
            if best_score is None or score > best_score:
                best_score = score
                best_position = (next_x, next_y)

        if best_position is None:
            return False
        self.x, self.y = best_position
        game_world.refresh_spatial_position(self)
        return True

    @staticmethod
    def _distance_to_segment(point_x, point_y, start_x, start_y, end_x, end_y):
        segment_x = end_x - start_x
        segment_y = end_y - start_y
        segment_length_squared = segment_x * segment_x + segment_y * segment_y
        if segment_length_squared == 0:
            return math.hypot(point_x - start_x, point_y - start_y)
        projection = (
            (point_x - start_x) * segment_x
            + (point_y - start_y) * segment_y
        ) / segment_length_squared
        projection = min(1.0, max(0.0, projection))
        closest_x = start_x + projection * segment_x
        closest_y = start_y + projection * segment_y
        return math.hypot(point_x - closest_x, point_y - closest_y)

    def set_screen_position(self, screen_x, screen_y):
        self._screen_position = (screen_x, screen_y)

    def update(self):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        self._update_attack_cooldown()
        direction_x = self.player.x - self.x
        direction_y = self.player.y - self.y
        distance = (direction_x**2 + direction_y**2) ** 0.5
        contact_distance = self.radius + self.player.radius
        if distance <= contact_distance + DISTANCE_EPSILON or distance == 0:
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self._attack_if_ready()
            return
        self.velocity_x = direction_x / distance
        self.velocity_y = direction_y / distance
        travel_distance = min(self._movement_per_frame, distance - contact_distance)
        self.move_towards(
            self.player.x,
            self.player.y,
            travel_distance,
        )
        distance = math.hypot(
            self.player.x - self.x,
            self.player.y - self.y,
        )
        if distance <= contact_distance + DISTANCE_EPSILON:
            self._attack_if_ready()

    def _update_attack_cooldown(self):
        self._attack_cooldown_frames = max(0.0, self._attack_cooldown_frames - 1.0)

    def _attack_if_ready(self):
        if self._attack_cooldown_frames > 0 or self.attack_damage <= 0:
            return False
        self.player.take_damage(self.attack_damage)
        self._attack_cooldown_frames = self.attack_interval * FPS
        return True

    def draw_health_bar(self, x, y, alpha=255):
        bar_width = self.radius * 2
        bar_height = 4
        bar_left = x - self.radius
        bar_bottom = y + self.radius + 3
        self.draw_rectangle(
            bar_left,
            bar_bottom,
            bar_left + bar_width * (self.hp / self.max_hp),
            bar_bottom + bar_height,
            255,
            0,
            0,
            alpha,
            True,
        )

    def draw(self):
        if self.image is None:
            raise RuntimeError("Enemy.draw requires a loaded enemy image")
        if self.draw_rectangle is None:
            raise RuntimeError("Enemy.draw requires a rectangle drawing function")
        x, y = self._screen_position or (self.x, self.y)
        self.image.draw(x, y, self.radius * 2, self.radius * 2)
        self.draw_health_bar(x, y)
