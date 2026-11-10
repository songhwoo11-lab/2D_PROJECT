"""Enemy archetypes backed by shared enemy behavior and stat data."""

import math

import pico2d

from arrow import Arrow
import game_world
from enemy import ENEMY_STATS, Enemy, EnemyType
from explosion import Explosion, ExplosionTarget
from game_config import DISTANCE_EPSILON, FPS


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
    FADE_DISTANCE = 150.0
    HEALTH_BAR_DISTANCE = 100.0
    HIT_FLASH_DURATION_SECONDS = 0.2

    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.ASSASSIN],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
        self._hit_flash_frames_remaining = 0

    @property
    def distance_to_player(self):
        if self.player is None:
            return 0.0
        return math.hypot(self.player.x - self.x, self.player.y - self.y)

    @property
    def opacity_alpha(self):
        if self._hit_flash_frames_remaining > 0:
            return 255
        opacity = min(
            max(1.0 - self.distance_to_player / self.FADE_DISTANCE, 0.0),
            1.0,
        )
        return round(opacity * 255)

    @property
    def health_bar_alpha(self):
        if (
            self.distance_to_player <= self.HEALTH_BAR_DISTANCE
            or self._hit_flash_frames_remaining > 0
        ):
            return 255
        return 0

    def take_damage(self, amount):
        was_alive = self.is_alive
        defeated = super().take_damage(amount)
        if amount > 0 and was_alive:
            self._hit_flash_frames_remaining = round(
                self.HIT_FLASH_DURATION_SECONDS * FPS
            )
        return defeated

    def update(self):
        self._hit_flash_frames_remaining = max(
            0,
            self._hit_flash_frames_remaining - 1,
        )
        super().update()

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


class ArcherEnemy(Enemy):
    CHARGE_SPEED_MULTIPLIER = 2
    WARNING_DURATION_FRAMES = 15

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
        self._attack_charge_frames = 0
        self.attack_warning_remaining = 0
        self.arrow_image = arrow_image

    @property
    def is_attack_warning(self):
        return self.attack_warning_remaining > 0

    def update(self):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        distance_x = self.player.x - self.x
        distance_y = self.player.y - self.y
        distance = math.hypot(distance_x, distance_y)
        if distance > self.stats.attack_range + DISTANCE_EPSILON:
            self.attack_charge = 0.0
            self._attack_charge_frames = 0
            self.attack_warning_remaining = 0
            if distance > 0:
                travel_distance = min(
                    self._movement_per_frame,
                    distance - self.stats.attack_range,
                )
                self.move_towards(
                    self.player.x,
                    self.player.y,
                    travel_distance,
                )
            return
        if self.is_attack_warning:
            self.attack_warning_remaining -= 1
            if self.attack_warning_remaining == 0:
                game_world.add_object(
                    Arrow(
                        self.x,
                        self.y,
                        self.player.x,
                        self.player.y,
                        self.arrow_image,
                        target=self.player,
                        damage=self.attack_damage,
                    ),
                    depth=2,
                )
                self.attack_charge = 0.0
                self._attack_charge_frames = 0
            return
        charge_duration_frames = (
            self.attack_interval * FPS / self.CHARGE_SPEED_MULTIPLIER
        )
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


class ExplosiveEnemy(Enemy):
    PLAYER_ATTACK_RADIUS = 50.0
    DEATH_EXPLOSION_RADIUS = 50.0
    EXPLOSION_DAMAGE = 15.0

    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.EXPLOSIVE],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )

    def update(self):
        if self.player is None or not self.is_alive or self.player.is_defeated:
            return
        self._update_attack_cooldown()
        distance_x = self.player.x - self.x
        distance_y = self.player.y - self.y
        distance = math.hypot(distance_x, distance_y)
        attack_range = self.stats.attack_range
        if distance > attack_range + DISTANCE_EPSILON:
            if distance > 0:
                travel_distance = min(
                    self._movement_per_frame,
                    distance - attack_range,
                )
                self.move_towards(
                    self.player.x,
                    self.player.y,
                    travel_distance,
                )
            return
        if self._attack_cooldown_frames <= 0:
            Explosion(
                self.x,
                self.y,
                self.PLAYER_ATTACK_RADIUS,
                self.EXPLOSION_DAMAGE,
                ExplosionTarget.PLAYER_ONLY,
                owner=self,
            ).apply(player=self.player)
            super().take_damage(self.hp)

    def take_damage(self, amount):
        was_alive = self.is_alive
        defeated = super().take_damage(amount)
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
                self.EXPLOSION_DAMAGE,
                ExplosionTarget.ENEMIES_ONLY,
                owner=self,
            ).apply(enemies=enemies)
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
    return enemy_class(x, y, **kwargs)
