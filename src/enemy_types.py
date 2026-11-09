"""Enemy archetypes backed by shared enemy behavior and stat data."""

import math

from enemy import ENEMY_STATS, Enemy, EnemyType
from game_config import FPS


class BasicEnemy(Enemy):
    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.BASIC],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )


class TankerEnemy(Enemy):
    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.TANKER],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )


class AssassinEnemy(Enemy):
    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.ASSASSIN],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )


class ArcherEnemy(Enemy):
    WARNING_DURATION_FRAMES = 15

    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.ARCHER],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
        self.attack_charge = 0.0
        self._attack_charge_frames = 0
        self.attack_warning_remaining = 0

    @property
    def is_attack_warning(self):
        return self.attack_warning_remaining > 0

    def update(self):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        distance_x = self.player.x - self.x
        distance_y = self.player.y - self.y
        distance = math.hypot(distance_x, distance_y)
        if distance > self.stats.attack_range:
            self.attack_charge = 0.0
            self._attack_charge_frames = 0
            self.attack_warning_remaining = 0
            if distance > 0:
                travel = min(
                    self._movement_per_frame,
                    distance - self.stats.attack_range,
                )
                self.x += distance_x / distance * travel
                self.y += distance_y / distance * travel
            return
        if self.is_attack_warning:
            self.attack_warning_remaining -= 1
            if self.attack_warning_remaining == 0:
                self.player.take_damage(self.attack_damage)
                self.attack_charge = 0.0
                self._attack_charge_frames = 0
            return
        charge_duration_frames = self.attack_interval * FPS
        self._attack_charge_frames += 1
        self.attack_charge = min(
            1.0,
            self._attack_charge_frames / charge_duration_frames,
        )
        if self._attack_charge_frames >= charge_duration_frames:
            self.attack_charge = 1.0
            self.attack_warning_remaining = self.WARNING_DURATION_FRAMES

    def draw(self):
        super().draw()
        if self.draw_rectangle is None:
            raise RuntimeError("ArcherEnemy.draw requires a rectangle drawing function")
        x, y = self._screen_position or (self.x, self.y)
        bar_width = self.radius * 2
        bar_left = x - self.radius
        bar_bottom = y + self.radius + 9
        color = (255, 80, 40) if self.is_attack_warning else (80, 200, 255)
        self.draw_rectangle(
            bar_left,
            bar_bottom,
            bar_left + bar_width * self.attack_charge,
            bar_bottom + 3,
            *color,
            255,
            True,
        )
