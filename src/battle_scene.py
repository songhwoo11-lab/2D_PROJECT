"""First-stage battle scene: movement, aiming, pistol controls, and HUD."""

from enum import Enum
import math
import random

from arrow import Arrow
import battle_record
from bullet import Bullet
from enemy import ENEMY_STATS, Enemy, EnemyType
from enemy_types import AssassinEnemy, create_enemy
import game_world
from game_camera import Camera
from game_config import (
    CHARACTER_SCALE,
    HEALTH_PICKUP_LIMIT,
    MAGAZINE_PICKUP_AMMO,
    PICKUP_DRAW_SIZE,
    PLAYER_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    UI_SCALE,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from hud import draw_centered_text, draw_hud
from player import Player
from pickup import (
    HealthPickup,
    MagazinePickup,
    roll_coin_reward,
    roll_health_drop,
    roll_magazine_drop,
)
from shot_result import HitResult
from spawn_warning import SpawnWarning
from waves import (
    WaveDirector,
    random_spawn_position,
    wave_stat_multiplier,
)
from weapon import Gun


SHOT_FEEDBACK_DURATION = 0.8
SHOT_FEEDBACK_COLOR = (255, 0, 0)
SHOT_FEEDBACK_FONT_SIZE = 12 * UI_SCALE
WAVE_BANNER_SECONDS = 2.5
WAVE_STRENGTH_BANNER_SECONDS = 3.5

PAUSE_MENU_ITEMS = ("RESUME", "QUIT TO LOBBY")
RESULT_TITLES = {
    "victory": "VICTORY",
    "defeat": "DEFEAT",
    "quit": "BATTLE ENDED",
}


class BattleResult(Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    QUIT = "quit"
DEBUG_MENU_WIDTH = 190 * UI_SCALE
DEBUG_MENU_LEFT = SCREEN_WIDTH - DEBUG_MENU_WIDTH - 8 * UI_SCALE
DEBUG_BUTTON_TOP = 42 * UI_SCALE
DEBUG_BUTTON_HEIGHT = 26 * UI_SCALE
DEBUG_BUTTON_SPACING = 30 * UI_SCALE
DEBUG_BUTTON_TEXT_Y_OFFSET = 5 * UI_SCALE
DEBUG_FONT_SIZE = 15 * UI_SCALE
DEBUG_MENU_ITEMS = (
    ("spawn_basic", "Basic Enemy"),
    ("spawn_explosive", "Explosive Enemy"),
    ("spawn_assassin", "Assassin Enemy"),
    ("spawn_archer", "Archer Enemy"),
    ("spawn_tanker", "Tanker Enemy"),
    ("remove_all_enemies", "Remove All Enemies"),
    ("reset_hp", "Reset Player HP"),
    ("reset_map", "Reset Map"),
    ("toggle_attack_ranges", "Attack Ranges: OFF"),
    ("toggle_hitboxes", "Hitboxes: OFF"),
    ("toggle_assassin_reveal_range", "Assassin Reveal: OFF"),
)


class BattleScene:
    def __init__(
        self,
        player,
        gun,
        background,
        camera=None,
        gun_image=None,
        bullet_image=None,
        hud_font=None,
        hit_feedback_font=None,
        debug_font=None,
        enemy_images=None,
        enemy_draw_rectangle=None,
        enemy_draw_circle=None,
        arrow_image=None,
        ammo_image=None,
        health_image=None,
        random_source=None,
        total_waves=None,
        wave_spawn_rate=None,
    ):
        self.player = player
        self.gun = gun
        self.background = background
        self.camera = camera or Camera()
        self.gun_image = gun_image
        self.bullet_image = bullet_image
        self.hud_font = hud_font
        self.hit_feedback_font = (
            hud_font if hit_feedback_font is None else hit_feedback_font
        )
        self.debug_font = hud_font if debug_font is None else debug_font
        self.enemy_images = dict(enemy_images or {})
        self.enemy_draw_rectangle = enemy_draw_rectangle
        self.enemy_draw_circle = enemy_draw_circle
        self.arrow_image = arrow_image
        self.ammo_image = ammo_image
        self.health_image = health_image
        self.initial_player_position = (player.x, player.y)
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.mouse_held = False
        self._mouse_pressed = False
        self.debug_mode = False
        self.show_attack_ranges = False
        self.show_hitboxes = False
        self.show_assassin_reveal_range = False
        self.shot_feedbacks = []
        self.random_source = random_source or random.Random()
        self.total_waves_setting = total_waves
        self.wave_spawn_rate_setting = wave_spawn_rate
        self.wave_director = self._create_wave_director()
        self.spawn_warnings = []
        self.wave_banner_text = ""
        self.wave_banner_remaining = 0.0
        self.waves_cleared = False
        self.elapsed_time = 0.0
        self.reached_wave = 1
        self.clear_time = None
        self.coins = 0
        self.pickups = []
        self.health_pickups = []
        self.paused = False
        self.pause_menu_index = 0
        self.finished = False
        self.result = None
        self.exit_requested = False

        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()
        self._announce_wave()

    def close(self):
        game_world.clear()

    def _create_wave_director(self):
        options = {"random_source": self.random_source}
        if self.total_waves_setting is not None:
            options["total_waves"] = self.total_waves_setting
        if self.wave_spawn_rate_setting is not None:
            options["spawn_rate"] = self.wave_spawn_rate_setting
        return WaveDirector(**options)

    def spawn_enemy(self, enemy_type, x, y):
        if enemy_type not in self.enemy_images:
            raise KeyError("missing image for enemy type: {}".format(enemy_type.value))
        if self.enemy_draw_rectangle is None:
            raise RuntimeError("BattleScene requires an enemy rectangle drawing function")
        enemy = create_enemy(
            enemy_type,
            x,
            y,
            self.enemy_images[enemy_type],
            self.player,
            self.enemy_draw_rectangle,
            arrow_image=self.arrow_image,
        )
        game_world.add_object(enemy, depth=1)
        return enemy

    def _announce_wave(self):
        wave = self.wave_director.current_wave
        if wave % 10 == 0:
            self.wave_banner_text = "WAVE {} - ENEMIES ARE STRONGER!".format(
                wave
            )
            self.wave_banner_remaining = WAVE_STRENGTH_BANNER_SECONDS
        else:
            self.wave_banner_text = "WAVE {}".format(wave)
            self.wave_banner_remaining = WAVE_BANNER_SECONDS

    def _spawn_wave_enemy(self, enemy_type, x, y):
        enemy = self.spawn_enemy(enemy_type, x, y)
        enemy.apply_stat_multiplier(
            wave_stat_multiplier(self.wave_director.current_wave)
        )
        return enemy

    def _magazine_pickup_amount(self):
        return MAGAZINE_PICKUP_AMMO

    def _reward_enemy_defeat(self, enemy):
        self.coins += roll_coin_reward(self.random_source)
        if roll_magazine_drop(self.gun.total_ammo, self.random_source):
            self.pickups.append(
                MagazinePickup(
                    enemy.x,
                    enemy.y,
                    self._magazine_pickup_amount(),
                    image=self.ammo_image,
                )
            )
        if (
            len(self.health_pickups) < HEALTH_PICKUP_LIMIT
            and roll_health_drop(
                self.player.hp,
                self.player.max_hp,
                self.random_source,
            )
        ):
            self.health_pickups.append(
                HealthPickup(enemy.x, enemy.y, image=self.health_image)
            )

    def _update_pickups(self):
        remaining = []
        for pickup in self.pickups:
            if pickup.can_collect(self.player):
                if self.gun.add_reserve_ammo(pickup.amount) > 0:
                    continue
            remaining.append(pickup)
        self.pickups = remaining
        remaining_health = []
        for pickup in self.health_pickups:
            if pickup.can_collect(self.player):
                if self.player.heal(pickup.amount) > 0:
                    continue
            remaining_health.append(pickup)
        self.health_pickups = remaining_health

    def _alive_enemy_count(self):
        return sum(
            1
            for layer in game_world.world
            for obj in layer
            if isinstance(obj, Enemy) and obj.is_alive
        )

    def _remaining_enemy_count(self):
        unspawned = (
            self.wave_director.total_to_spawn
            - self.wave_director.spawned_count
        )
        return self._alive_enemy_count() + len(self.spawn_warnings) + unspawned

    def _update_waves(self, delta_time):
        if self.waves_cleared:
            return
        for enemy_type in self.wave_director.pending_spawns(delta_time):
            x, y = random_spawn_position(
                enemy_type,
                self.player.x,
                self.player.y,
                WORLD_WIDTH,
                WORLD_HEIGHT,
                self.random_source,
            )
            self.spawn_warnings.append(
                (
                    SpawnWarning(x, y, ENEMY_STATS[enemy_type].radius),
                    enemy_type,
                    x,
                    y,
                )
            )
        active_warnings = []
        expired_warnings = []
        for entry in self.spawn_warnings:
            entry[0].update(delta_time)
            if entry[0].is_expired:
                expired_warnings.append(entry)
            else:
                active_warnings.append(entry)
        self.spawn_warnings = active_warnings
        for _, enemy_type, x, y in expired_warnings:
            self._spawn_wave_enemy(enemy_type, x, y)
        if (
            self.wave_director.all_spawned
            and not self.spawn_warnings
            and self._alive_enemy_count() == 0
        ):
            if self.wave_director.advance():
                self.reached_wave = self.wave_director.current_wave
                self._announce_wave()
            else:
                self.waves_cleared = True
                self.wave_banner_text = "ALL WAVES CLEARED"
                self.wave_banner_remaining = WAVE_STRENGTH_BANNER_SECONDS

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.finished:
            if key in ("return", "enter"):
                self.exit_requested = True
            return
        if key == "q":
            self.paused = not self.paused
            if self.paused:
                self.pause_menu_index = 0
            return
        if self.paused:
            if key in ("w", "up"):
                self.pause_menu_index = (
                    self.pause_menu_index - 1
                ) % len(PAUSE_MENU_ITEMS)
            elif key in ("s", "down"):
                self.pause_menu_index = (
                    self.pause_menu_index + 1
                ) % len(PAUSE_MENU_ITEMS)
            elif key in ("return", "enter"):
                self._select_pause_menu_item()
            elif key == "escape":
                self.paused = False
            return
        if key == "f1":
            self.debug_mode = not self.debug_mode
            self.gun.infinite_ammo = self.debug_mode
            self.gun.heat_enabled = not self.debug_mode
        elif key == "e":
            self.gun.toggle_mode()
        elif key == "r":
            self.gun.start_reload()

    def _select_pause_menu_item(self):
        if self.pause_menu_index == 0:
            self.paused = False
        else:
            self._finish(BattleResult.QUIT)

    def _finish(self, result):
        if self.finished:
            return
        self.finished = True
        self.result = result
        self.paused = False
        if result is BattleResult.VICTORY:
            self.clear_time = self.elapsed_time

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if (
            button == "left"
            and self.debug_mode
            and screen_x is not None
            and screen_y is not None
            and self._handle_debug_click(screen_x, screen_y)
        ):
            return
        if button == "left" and not self.mouse_held:
            self.mouse_held = True
            self._mouse_pressed = True

    def mouse_up(self, button):
        if button == "left":
            self.mouse_held = False

    def _debug_button_bounds(self, index):
        top = DEBUG_BUTTON_TOP + index * DEBUG_BUTTON_SPACING
        return (
            DEBUG_MENU_LEFT + 8 * UI_SCALE,
            top,
            SCREEN_WIDTH - 8 * UI_SCALE,
            top + DEBUG_BUTTON_HEIGHT,
        )

    def _handle_debug_click(self, screen_x, screen_y):
        menu_bottom = DEBUG_BUTTON_TOP + len(DEBUG_MENU_ITEMS) * DEBUG_BUTTON_SPACING
        if not (
            DEBUG_MENU_LEFT <= screen_x <= SCREEN_WIDTH - 8 * UI_SCALE
            and 8 * UI_SCALE <= screen_y <= menu_bottom
        ):
            return False

        for index, (action, _) in enumerate(self._debug_menu_items()):
            left, top, right, bottom = self._debug_button_bounds(index)
            if left <= screen_x <= right and top <= screen_y <= bottom:
                self._run_debug_action(action)
                return True
        return True

    def _run_debug_action(self, action):
        enemy_types = {
            "spawn_basic": EnemyType.BASIC,
            "spawn_explosive": EnemyType.EXPLOSIVE,
            "spawn_assassin": EnemyType.ASSASSIN,
            "spawn_archer": EnemyType.ARCHER,
            "spawn_tanker": EnemyType.TANKER,
        }
        if action in enemy_types:
            self.spawn_enemy(
                enemy_types[action],
                WORLD_WIDTH / 2,
                WORLD_HEIGHT / 2,
            )
        elif action == "reset_hp":
            self.player.hp = self.player.max_hp
            self.player.reset_hp_trail()
        elif action == "reset_map":
            self.reset_map()
        elif action == "remove_all_enemies":
            self._remove_all_enemies()
        elif action == "toggle_attack_ranges":
            self.show_attack_ranges = not self.show_attack_ranges
        elif action == "toggle_hitboxes":
            self.show_hitboxes = not self.show_hitboxes
        elif action == "toggle_assassin_reveal_range":
            self.show_assassin_reveal_range = not self.show_assassin_reveal_range

    def _remove_all_enemies(self):
        enemies = [
            obj
            for layer in game_world.world
            for obj in tuple(layer)
            if isinstance(obj, Enemy)
        ]
        for enemy in enemies:
            game_world.remove_object(enemy)

    def reset_map(self):
        self.player.x, self.player.y = self.initial_player_position
        self.player.hp = self.player.max_hp
        self.player.reset_hp_trail()
        self.player.aim_angle = 0.0
        self.player.set_movement(0, 0, 0.0)
        self.gun.reset()
        self.gun.infinite_ammo = self.debug_mode
        self.gun.heat_enabled = not self.debug_mode
        self.keys.clear()
        self.mouse_held = False
        self._mouse_pressed = False
        self.show_attack_ranges = False
        self.show_hitboxes = False
        self.show_assassin_reveal_range = False
        self.wave_director = self._create_wave_director()
        self.spawn_warnings = []
        self.waves_cleared = False
        self.elapsed_time = 0.0
        self.reached_wave = 1
        self.clear_time = None
        self.coins = 0
        self.pickups = []
        self.health_pickups = []
        self.paused = False
        self.pause_menu_index = 0
        self.finished = False
        self.result = None
        self.exit_requested = False
        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()
        self._announce_wave()

    def update(self, delta_time):
        if self.finished or self.paused:
            return
        self.elapsed_time += delta_time
        self.shot_feedbacks = [
            (x, y, label, remaining - delta_time)
            for x, y, label, remaining in self.shot_feedbacks
            if remaining > delta_time
        ]
        self.gun.update(delta_time)
        move_x = int("d" in self.keys) - int("a" in self.keys)
        move_y = int("w" in self.keys) - int("s" in self.keys)
        self.player.set_movement(move_x, move_y, delta_time)
        bullets = [
            obj
            for layer in game_world.world
            for obj in layer
            if isinstance(obj, Bullet)
        ]
        game_world.update()
        self._update_hp_trails(delta_time)
        self._record_shot_feedback(bullets)
        if self.player.is_defeated:
            self._finish(BattleResult.DEFEAT)
            return

        self.camera.follow(self.player.x, self.player.y)
        world_x, world_y = self.camera.screen_to_world(
            self.mouse_screen_x,
            self.mouse_screen_y,
            origin_top=True,
        )
        self.player.aim_at(world_x, world_y)
        self._update_player_view()

        fired = self.gun.handle_fire_input(
            mouse_held=self.mouse_held,
            mouse_pressed=self._mouse_pressed,
        )
        self._mouse_pressed = False
        if fired:
            if self.bullet_image is not None:
                muzzle_offset = PLAYER_RADIUS + 14 * UI_SCALE
                game_world.add_object(
                    Bullet(
                        self.player.x
                        + math.cos(self.player.aim_angle) * muzzle_offset,
                        self.player.y
                        + math.sin(self.player.aim_angle) * muzzle_offset,
                        self.player.aim_angle,
                        self.bullet_image,
                        damage=self.gun.effective_damage,
                    ),
                    depth=2,
                )
        self._remove_defeated_enemies()
        self._update_pickups()
        self._update_waves(delta_time)
        self.wave_banner_remaining = max(
            0.0,
            self.wave_banner_remaining - delta_time,
        )
        if self.waves_cleared:
            self._finish(BattleResult.VICTORY)

    def _record_shot_feedback(self, bullets):
        result_labels = {
            HitResult.HIT: "HIT",
            HitResult.HEADSHOT: "HEADSHOT",
            HitResult.MISS: "MISS",
        }
        for bullet in bullets:
            if bullet.hit_target is None or bullet.hit_result is None:
                continue
            target = bullet.hit_target
            self.shot_feedbacks.append(
                (
                    target.x - target.radius,
                    target.y + target.radius + 4 * UI_SCALE,
                    result_labels[bullet.hit_result],
                    SHOT_FEEDBACK_DURATION,
                )
            )

    def _update_hp_trails(self, delta_time):
        self.player.update_hp_trail(delta_time)
        for layer in game_world.world:
            for obj in layer:
                if isinstance(obj, Enemy):
                    obj.update_hp_trail(delta_time)

    def _remove_defeated_enemies(self):
        defeated = [
            obj
            for layer in game_world.world
            for obj in tuple(layer)
            if isinstance(obj, Enemy) and not obj.is_alive
        ]
        for enemy in defeated:
            self._reward_enemy_defeat(enemy)
            game_world.remove_object(enemy)

    def _update_player_view(self):
        screen_x, screen_y = self.camera.world_to_screen(self.player.x, self.player.y)
        self.player.set_screen_position(screen_x, screen_y)

    def draw(self, draw_rectangle):
        first_column = int(self.camera.x // SCREEN_WIDTH)
        last_column = int((self.camera.x + SCREEN_WIDTH) // SCREEN_WIDTH)
        first_row = int(self.camera.y // SCREEN_HEIGHT)
        last_row = int((self.camera.y + SCREEN_HEIGHT) // SCREEN_HEIGHT)

        for row in range(first_row, last_row + 1):
            for column in range(first_column, last_column + 1):
                screen_x = column * SCREEN_WIDTH - self.camera.x + SCREEN_WIDTH / 2
                screen_y = row * SCREEN_HEIGHT - self.camera.y + SCREEN_HEIGHT / 2
                self.background.draw(screen_x, screen_y, SCREEN_WIDTH, SCREEN_HEIGHT)

        for layer in game_world.world:
            for obj in layer:
                if isinstance(obj, (Arrow, Bullet, Enemy)):
                    screen_x, screen_y = self.camera.world_to_screen(obj.x, obj.y)
                    obj.set_screen_position(screen_x, screen_y)
        game_world.render(self._is_visible_on_screen)
        self._draw_spawn_warnings()
        self._draw_pickups(draw_rectangle)
        for x, y, label, _ in self.shot_feedbacks:
            screen_x, screen_y = self.camera.world_to_screen(x, y)
            self.hit_feedback_font.draw(
                screen_x,
                screen_y,
                label,
                SHOT_FEEDBACK_COLOR,
            )
        if (
            self.show_attack_ranges
            or self.show_hitboxes
            or self.show_assassin_reveal_range
        ):
            self._draw_enemy_debug_circles()
        if self.gun_image is not None:
            gun_offset = PLAYER_RADIUS * 0.6
            gun_x = (
                self.player.screen_position[0]
                + math.cos(self.player.aim_angle) * gun_offset
            )
            gun_y = (
                self.player.screen_position[1]
                + math.sin(self.player.aim_angle) * gun_offset
            )
            gun_angle = self.player.aim_angle
            flip = ""
            if gun_angle > math.pi / 2:
                gun_angle -= math.pi
                flip = "h"
            elif gun_angle < -math.pi / 2:
                gun_angle += math.pi
                flip = "h"
            self.gun_image.composite_draw(
                gun_angle,
                flip,
                gun_x,
                gun_y,
                42 * UI_SCALE * CHARACTER_SCALE,
                24 * UI_SCALE * CHARACTER_SCALE,
            )
        if self.hud_font is None:
            raise RuntimeError("BattleScene.draw requires a loaded HUD font")
        self._draw_wave_banner()
        draw_hud(
            self.player,
            self.gun,
            self.hud_font,
            draw_rectangle,
            wave=self.wave_director.current_wave,
            total_waves=self.wave_director.total_waves,
            coins=self.coins,
            remaining_enemies=self._remaining_enemy_count(),
        )
        if self.debug_mode:
            self._draw_debug_menu(draw_rectangle)
        if self.paused:
            self._draw_pause_menu(draw_rectangle)
        if self.finished:
            self._draw_result_screen(draw_rectangle)

    def _draw_spawn_warnings(self):
        if self.enemy_draw_circle is None:
            return
        for warning, _, _, _ in self.spawn_warnings:
            screen_x, screen_y = self.camera.world_to_screen(
                warning.x,
                warning.y,
            )
            margin = warning.radius + 20 * UI_SCALE
            if not (
                -margin <= screen_x <= SCREEN_WIDTH + margin
                and -margin <= screen_y <= SCREEN_HEIGHT + margin
            ):
                continue
            self.enemy_draw_circle(
                screen_x,
                screen_y,
                round(warning.radius + 6 * UI_SCALE * warning.progress),
                255,
                60,
                60,
                200,
            )

    def _draw_pause_menu(self, draw_rectangle):
        left = SCREEN_WIDTH / 2 - 150 * UI_SCALE
        right = SCREEN_WIDTH / 2 + 150 * UI_SCALE
        bottom = SCREEN_HEIGHT / 2 - 85 * UI_SCALE
        top = SCREEN_HEIGHT / 2 + 85 * UI_SCALE
        draw_rectangle(left, bottom, right, top, 20, 25, 35, 225, True)
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT / 2 + 52 * UI_SCALE,
            "PAUSED",
            (255, 220, 80),
        )
        for index, label in enumerate(PAUSE_MENU_ITEMS):
            color = (
                (255, 220, 80)
                if index == self.pause_menu_index
                else (255, 255, 255)
            )
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT / 2 + 12 * UI_SCALE - index * 34 * UI_SCALE,
                label,
                color,
            )

    def _draw_result_screen(self, draw_rectangle):
        draw_rectangle(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            0,
            0,
            0,
            180,
            True,
        )
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT / 2 + 40 * UI_SCALE,
            RESULT_TITLES[self.result.value],
            (255, 220, 80),
        )
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT / 2,
            battle_record.result_record_text(
                self.result.value,
                self.reached_wave,
                self.wave_director.total_waves,
                self.elapsed_time,
                self.clear_time,
            ),
            (255, 255, 255),
        )
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT / 2 - 40 * UI_SCALE,
            "PRESS ENTER TO RETURN TO LOBBY",
            (255, 255, 255),
        )

    def _draw_pickups(self, draw_rectangle):
        groups = (
            (self.pickups, (235, 190, 65)),
            (self.health_pickups, (235, 70, 70)),
        )
        for pickups, color in groups:
            for pickup in pickups:
                screen_x, screen_y = self.camera.world_to_screen(
                    pickup.x,
                    pickup.y,
                )
                if not (
                    -PICKUP_DRAW_SIZE <= screen_x <= SCREEN_WIDTH + PICKUP_DRAW_SIZE
                    and -PICKUP_DRAW_SIZE
                    <= screen_y
                    <= SCREEN_HEIGHT + PICKUP_DRAW_SIZE
                ):
                    continue
                if pickup.draw(screen_x, screen_y):
                    continue
                draw_rectangle(
                    screen_x - pickup.radius,
                    screen_y - pickup.radius,
                    screen_x + pickup.radius,
                    screen_y + pickup.radius,
                    color[0],
                    color[1],
                    color[2],
                    255,
                    True,
                )

    def _draw_wave_banner(self):
        if self.wave_banner_remaining <= 0.0 or not self.wave_banner_text:
            return
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT - 130 * UI_SCALE,
            self.wave_banner_text,
            (255, 220, 80),
        )

    @staticmethod
    def _is_visible_on_screen(obj):
        screen_position = getattr(obj, "_screen_position", None)
        if screen_position is None:
            x, y = obj.x, obj.y
        else:
            x, y = screen_position
        margin = max(getattr(obj, "radius", 0), 12 * UI_SCALE)
        return (
            -margin <= x <= SCREEN_WIDTH + margin
            and -margin <= y <= SCREEN_HEIGHT + margin
        )

    def _debug_menu_items(self):
        toggle_states = {
            "toggle_attack_ranges": self.show_attack_ranges,
            "toggle_hitboxes": self.show_hitboxes,
            "toggle_assassin_reveal_range": self.show_assassin_reveal_range,
        }
        return tuple(
            (
                action,
                label.replace("OFF", "ON" if toggle_states[action] else "OFF")
                if action in toggle_states
                else label,
            )
            for action, label in DEBUG_MENU_ITEMS
        )

    def _draw_debug_menu(self, draw_rectangle):
        if self.debug_font is None:
            raise RuntimeError("BattleScene debug menu requires a loaded debug font")
        menu_bottom = DEBUG_BUTTON_TOP + len(DEBUG_MENU_ITEMS) * DEBUG_BUTTON_SPACING
        draw_rectangle(
            DEBUG_MENU_LEFT,
            SCREEN_HEIGHT - menu_bottom - 8 * UI_SCALE,
            SCREEN_WIDTH - 8 * UI_SCALE,
            SCREEN_HEIGHT - 8 * UI_SCALE,
            25,
            30,
            40,
            230,
            True,
        )
        self.debug_font.draw(
            DEBUG_MENU_LEFT + 8 * UI_SCALE,
            SCREEN_HEIGHT - 30 * UI_SCALE,
            "DEBUG MODE",
            (255, 220, 80),
        )
        for index, (_, label) in enumerate(self._debug_menu_items()):
            left, top, right, bottom = self._debug_button_bounds(index)
            text_y = (
                SCREEN_HEIGHT
                - bottom
                + (DEBUG_BUTTON_HEIGHT - DEBUG_FONT_SIZE) // 2
                + DEBUG_BUTTON_TEXT_Y_OFFSET
            )
            self.debug_font.draw(
                left + 6 * UI_SCALE,
                text_y,
                label,
                (255, 255, 255),
            )
            draw_rectangle(
                left,
                SCREEN_HEIGHT - bottom,
                right,
                SCREEN_HEIGHT - top,
                65,
                75,
                90,
                255,
                False,
            )

    def _draw_enemy_debug_circles(self):
        if self.enemy_draw_circle is None:
            raise RuntimeError(
                "BattleScene debug visualization requires a circle drawing function"
            )
        for layer in game_world.world:
            for enemy in layer:
                if not isinstance(enemy, Enemy):
                    continue
                x, y = enemy._screen_position or self.camera.world_to_screen(
                    enemy.x,
                    enemy.y,
                )
                if self.show_hitboxes:
                    self.enemy_draw_circle(
                        x,
                        y,
                        round(enemy.radius),
                        0,
                        0,
                        255,
                        255,
                    )
                if self.show_attack_ranges:
                    attack_range = (
                        enemy.stats.attack_range
                        or enemy.radius + self.player.radius
                    )
                    self.enemy_draw_circle(
                        x,
                        y,
                        round(attack_range),
                        255,
                        0,
                        0,
                        255,
                    )
        if self.show_hitboxes:
            player_x, player_y = self.camera.world_to_screen(
                self.player.x,
                self.player.y,
            )
            self.enemy_draw_circle(
                player_x,
                player_y,
                round(self.player.radius),
                0,
                0,
                255,
                255,
            )
        if self.show_assassin_reveal_range:
            player_x, player_y = self.camera.world_to_screen(
                self.player.x,
                self.player.y,
            )
            self.enemy_draw_circle(
                player_x,
                player_y,
                round(AssassinEnemy.FADE_DISTANCE),
                255,
                255,
                0,
                255,
            )
