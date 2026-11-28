"""Enemy archetypes backed by shared enemy behavior and stat data."""

import math

import pico2d

from arrow import Arrow
import game_world
from enemy import ENEMY_STATS, DAMAGE_SOURCE_EXPLOSION, Enemy, EnemyType
from explosion import Explosion, ExplosionTarget
from game_config import DISTANCE_EPSILON


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
    FADE_DISTANCE = 350.0
    HEALTH_BAR_DISTANCE = 200.0
    HIT_FLASH_DURATION_SECONDS = 0.2
    ATTACK_LENGTH = 400.0
    PREPARE_DURATION_SECONDS = 1.0
    TRACK_DURATION_SECONDS = 0.5
    STRIKE_VISIBLE_SECONDS = 0.2
    STRIKE_WIDTH = 5.0

    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.ASSASSIN],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
        # 암살자는 다른 적과 충돌하지 않고, 다른 적도 암살자를 피하지 않는다.
        self._uses_spatial_collision = False
        self._checks_enemy_collisions = False
        self._hit_flash_remaining = 0.0
        self._attack_prepare_remaining = 0.0
        self._attack_direction = (1.0, 0.0)
        self._strike_remaining = 0.0
        self._strike_origin = (self.x, self.y)
        self._strike_direction = self._attack_direction

    @property
    def distance_to_player(self):
        if self.player is None:
            return 0.0
        return math.hypot(self.player.x - self.x, self.player.y - self.y)

    @property
    def is_attack_visible(self):
        return self.is_preparing_attack or self.is_strike_visible

    @property
    def opacity_alpha(self):
        # 체력바가 보이거나 직선 공격 중에는 암살자도 완전히 드러낸다.
        if self.is_attack_visible or self._hit_flash_remaining > 0 or self.health_bar_alpha > 0:
            return 255
        opacity = min(
            max(1.0 - self.distance_to_player / self.FADE_DISTANCE, 0.0),
            1.0,
        )
        return round(opacity * 255)

    @property
    def health_bar_alpha(self):
        if (
            self.is_attack_visible
            or self.distance_to_player <= self.HEALTH_BAR_DISTANCE
            or self._hit_flash_remaining > 0
        ):
            return 255
        return 0

    def take_damage(self, amount, source=None):
        was_alive = self.is_alive
        defeated = super().take_damage(amount, source=source)
        if amount > 0 and was_alive:
            self._hit_flash_remaining = self.HIT_FLASH_DURATION_SECONDS
        return defeated

    @property
    def is_fully_visible(self):
        if self.player is None:
            return False
        return self.health_bar_alpha > 0

    @property
    def is_preparing_attack(self):
        return self._attack_prepare_remaining > 0

    @property
    def attack_prepare_progress(self):
        if not self.is_preparing_attack:
            return 0.0
        return min(
            1.0,
            1.0 - self._attack_prepare_remaining / self.PREPARE_DURATION_SECONDS,
        )

    @property
    def attack_direction(self):
        return self._attack_direction

    @property
    def is_strike_visible(self):
        return self._strike_remaining > 0

    def update(self, delta_time):
        self._hit_flash_remaining = max(
            0.0,
            self._hit_flash_remaining - delta_time,
        )
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        self._update_attack_cooldown(delta_time)
        self._strike_remaining = max(0.0, self._strike_remaining - delta_time)

        if self.is_preparing_attack:
            self._advance_attack_preparation(delta_time)
            return

        if self._is_touching_player():
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self._attack_if_ready()
            return

        if self.is_fully_visible and self._attack_cooldown_remaining <= 0:
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self._attack_prepare_remaining = self.PREPARE_DURATION_SECONDS
            self._advance_attack_preparation(delta_time)
            return
        self._move_toward_player(delta_time)

    def _is_touching_player(self):
        distance = math.hypot(self.player.x - self.x, self.player.y - self.y)
        contact_distance = self.radius + self.player.radius
        return distance <= contact_distance + DISTANCE_EPSILON or distance == 0

    def _advance_attack_preparation(self, delta_time):
        elapsed = self.PREPARE_DURATION_SECONDS - self._attack_prepare_remaining
        if elapsed < self.TRACK_DURATION_SECONDS:
            self._aim_at_player()
        self._attack_prepare_remaining = max(
            0.0,
            self._attack_prepare_remaining - delta_time,
        )
        if self._attack_prepare_remaining <= 0:
            self._fire_strike()

    def _aim_at_player(self):
        direction_x = self.player.x - self.x
        direction_y = self.player.y - self.y
        distance = math.hypot(direction_x, direction_y)
        if distance <= 0:
            return
        self._attack_direction = (direction_x / distance, direction_y / distance)

    def _strike_end(self):
        origin_x, origin_y = self._strike_origin
        direction_x, direction_y = self._strike_direction
        return (
            origin_x + direction_x * self.ATTACK_LENGTH,
            origin_y + direction_y * self.ATTACK_LENGTH,
        )

    def _fire_strike(self):
        self._strike_origin = (self.x, self.y)
        self._strike_direction = self._attack_direction
        self._strike_remaining = self.STRIKE_VISIBLE_SECONDS
        self._attack_cooldown_remaining = self.attack_interval
        end_x, end_y = self._strike_end()
        if self._player_on_strike_line(end_x, end_y):
            self.player.take_damage(self.attack_damage)
        self.x = end_x
        self.y = end_y
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        game_world.refresh_spatial_position(self)

    def _player_on_strike_line(self, end_x, end_y):
        origin_x, origin_y = self._strike_origin
        distance = Enemy._distance_to_segment(
            self.player.x,
            self.player.y,
            origin_x,
            origin_y,
            end_x,
            end_y,
        )
        return distance <= self.player.radius + self.STRIKE_WIDTH / 2.0

    def _draw_strike_line(self, screen_x, screen_y, direction, color):
        direction_x, direction_y = direction
        end_x = screen_x + direction_x * self.ATTACK_LENGTH
        end_y = screen_y + direction_y * self.ATTACK_LENGTH
        length = math.hypot(direction_x, direction_y)
        if length == 0:
            pico2d.draw_line(screen_x, screen_y, end_x, end_y, *color, 255)
            return
        perpendicular_x = -direction_y / length
        perpendicular_y = direction_x / length
        half_offset = int((self.STRIKE_WIDTH - 1) / 2.0)
        for offset in range(-half_offset, half_offset + 1):
            offset_x = perpendicular_x * offset
            offset_y = perpendicular_y * offset
            pico2d.draw_line(
                screen_x + offset_x,
                screen_y + offset_y,
                end_x + offset_x,
                end_y + offset_y,
                *color,
                255,
            )

    def draw(self):
        if self.image is None:
            raise RuntimeError("AssassinEnemy.draw requires a loaded enemy image")
        if self.draw_rectangle is None:
            raise RuntimeError(
                "AssassinEnemy.draw requires a rectangle drawing function"
            )

        alpha = self.opacity_alpha
        if alpha == 0:
            return

        texture = self.image.texture
        if pico2d.SDL_SetTextureBlendMode(
            texture,
            pico2d.SDL_BLENDMODE_BLEND,
        ) != 0:
            raise RuntimeError(
                "Unable to enable assassin sprite blending: {}".format(
                    pico2d.SDL_GetError()
                )
            )
        if pico2d.SDL_SetTextureAlphaMod(texture, alpha) != 0:
            raise RuntimeError(
                "Unable to set assassin sprite opacity: {}".format(
                    pico2d.SDL_GetError()
                )
            )

        x, y = self._screen_position or (self.x, self.y)
        try:
            self.image.draw(x, y, self.radius * 2, self.radius * 2)
        finally:
            if pico2d.SDL_SetTextureAlphaMod(texture, 255) != 0:
                raise RuntimeError(
                    "Unable to restore assassin sprite opacity: {}".format(
                        pico2d.SDL_GetError()
                    )
                )
        health_bar_alpha = self.health_bar_alpha
        if health_bar_alpha > 0:
            self.draw_health_bar(x, y, health_bar_alpha)

        if self.is_preparing_attack:
            locked = self.attack_prepare_progress >= (
                self.TRACK_DURATION_SECONDS / self.PREPARE_DURATION_SECONDS
            )
            color = (255, 70, 60) if locked else (255, 200, 60)
            self._draw_strike_line(x, y, self._attack_direction, color)
        if self.is_strike_visible:
            origin_x, origin_y = self._strike_origin
            line_x = x + (origin_x - self.x)
            line_y = y + (origin_y - self.y)
            self._draw_strike_line(
                line_x,
                line_y,
                self._strike_direction,
                (255, 245, 150),
            )


class ArcherEnemy(Enemy):
    CHARGE_SPEED_MULTIPLIER = 2
    WARNING_DURATION_SECONDS = 15.0 / 60.0
    ARROW_MAX_DISTANCE = 1200.0

    def __init__(
        self,
        x,
        y,
        image=None,
        player=None,
        draw_rectangle=None,
        arrow_image=None,
    ):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.ARCHER],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
        self.attack_charge = 0.0
        self._attack_charge_elapsed = 0.0
        self.attack_warning_remaining = 0.0
        self.arrow_image = arrow_image

    @property
    def is_attack_warning(self):
        return self.attack_warning_remaining > 0

    def update(self, delta_time):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        charge_duration = (
            self.attack_interval / self.CHARGE_SPEED_MULTIPLIER
        )
        distance_x = self.player.x - self.x
        distance_y = self.player.y - self.y
        distance = math.hypot(distance_x, distance_y)
        if distance > self.stats.attack_range + DISTANCE_EPSILON:
            if not self.is_attack_warning and self.attack_charge > 0:
                self._attack_charge_elapsed = max(
                    0.0,
                    self._attack_charge_elapsed - delta_time,
                )
                self.attack_charge = (
                    self._attack_charge_elapsed / charge_duration
                )
            elif self.is_attack_warning:
                self._advance_attack_warning(delta_time)
            if distance > 0:
                travel_distance = min(
                    self.move_speed * delta_time,
                    distance - self.stats.attack_range,
                )
                self.move_towards(
                    self.player.x,
                    self.player.y,
                    travel_distance,
                )
            return
        if self.is_attack_warning:
            self._advance_attack_warning(delta_time)
            return
        self._attack_charge_elapsed += delta_time
        self.attack_charge = min(
            1.0,
            self._attack_charge_elapsed / charge_duration,
        )
        if self._attack_charge_elapsed >= charge_duration:
            self.attack_charge = 1.0
            self.attack_warning_remaining = self.WARNING_DURATION_SECONDS

    def _advance_attack_warning(self, delta_time):
        self.attack_warning_remaining = max(
            0.0,
            self.attack_warning_remaining - delta_time,
        )
        if self.attack_warning_remaining <= 0:
            game_world.add_object(
                Arrow(
                    self.x,
                    self.y,
                    self.player.x,
                    self.player.y,
                    self.arrow_image,
                    target=self.player,
                    damage=self.attack_damage,
                    max_distance=self.ARROW_MAX_DISTANCE,
                ),
                depth=2,
            )
            self.attack_charge = 0.0
            self._attack_charge_elapsed = 0.0

    def draw(self):
        super().draw()
        if self.draw_rectangle is None:
            raise RuntimeError("ArcherEnemy.draw requires a rectangle drawing function")
        x, y = self._screen_position or (self.x, self.y)
        bar_width = self.radius * 2
        bar_left = x - self.radius
        bar_bottom = y + self.radius + 18
        color = (255, 220, 40) if self.is_attack_warning else (80, 200, 255)
        self.draw_rectangle(
            bar_left,
            bar_bottom,
            bar_left + bar_width * self.attack_charge,
            bar_bottom + 6,
            *color,
            255,
            True,
        )


class ExplosiveEnemy(Enemy):
    PLAYER_ATTACK_RADIUS = 200.0
    DEATH_EXPLOSION_RADIUS = 200.0

    def __init__(
        self,
        x,
        y,
        image=None,
        player=None,
        draw_rectangle=None,
        on_explode=None,
    ):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.EXPLOSIVE],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
        self.on_explode = on_explode

    def update(self, delta_time):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        self._update_attack_cooldown(delta_time)
        distance_x = self.player.x - self.x
        distance_y = self.player.y - self.y
        distance = math.hypot(distance_x, distance_y)
        attack_range = self.stats.attack_range
        if distance > attack_range + DISTANCE_EPSILON:
            if distance > 0:
                travel_distance = min(
                    self.move_speed * delta_time,
                    distance - attack_range,
                )
                self.move_towards(
                    self.player.x,
                    self.player.y,
                    travel_distance,
                )
            return
        if self._attack_cooldown_remaining <= 0:
            Explosion(
                self.x,
                self.y,
                self.PLAYER_ATTACK_RADIUS,
                self.attack_damage,
                ExplosionTarget.PLAYER_ONLY,
                owner=self,
            ).apply(player=self.player)
            self._notify_explosion()
            super().take_damage(
                self.hp,
                source=DAMAGE_SOURCE_EXPLOSION,
            )

    def _notify_explosion(self):
        """Notify listeners once for each explosion caused by this enemy."""
        if self.on_explode is not None:
            self.on_explode()

    def take_damage(self, amount, source=None):
        was_alive = self.is_alive
        defeated = super().take_damage(amount, source=source)
        if was_alive and defeated:
            enemies = (
                obj
                for layer in game_world.world
                for obj in layer
                if isinstance(obj, Enemy) and obj is not self
            )
            Explosion(
                self.x,
                self.y,
                self.DEATH_EXPLOSION_RADIUS,
                self.attack_damage,
                ExplosionTarget.ENEMIES_ONLY,
                owner=self,
            ).apply(enemies=enemies)
            self._notify_explosion()
        return defeated


ENEMY_CLASSES = {
    EnemyType.BASIC: BasicEnemy,
    EnemyType.EXPLOSIVE: ExplosiveEnemy,
    EnemyType.TANKER: TankerEnemy,
    EnemyType.ASSASSIN: AssassinEnemy,
    EnemyType.ARCHER: ArcherEnemy,
}


def create_enemy(
    enemy_type,
    x,
    y,
    image,
    player,
    draw_rectangle,
    arrow_image=None,
    on_explode=None,
):
    try:
        enemy_class = ENEMY_CLASSES[enemy_type]
    except KeyError as error:
        raise ValueError("unsupported enemy type: {!r}".format(enemy_type)) from error
    kwargs = {
        "image": image,
        "player": player,
        "draw_rectangle": draw_rectangle,
    }
    if enemy_type is EnemyType.ARCHER:
        kwargs["arrow_image"] = arrow_image
    if enemy_type is EnemyType.EXPLOSIVE and on_explode is not None:
        kwargs["on_explode"] = on_explode
    return enemy_class(x, y, **kwargs)
