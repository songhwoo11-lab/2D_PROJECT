"""First-stage battle scene: movement, aiming, pistol controls, and HUD."""

import math

from arrow import Arrow
from bullet import Bullet
from enemy import Enemy, EnemyType
from enemy_types import create_enemy
import game_world
from game_camera import Camera
from game_config import (
    PLAYER_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from hud import draw_hud
from player import Player
from weapon import Gun


DEBUG_MENU_WIDTH = 190
DEBUG_MENU_LEFT = SCREEN_WIDTH - DEBUG_MENU_WIDTH - 8
DEBUG_BUTTON_TOP = 42
DEBUG_BUTTON_HEIGHT = 26
DEBUG_BUTTON_SPACING = 30
DEBUG_MENU_ITEMS = (
    ("spawn_basic", "Basic Enemy"),
    ("spawn_explosive", "Explosive Enemy"),
    ("spawn_assassin", "Assassin Enemy"),
    ("spawn_archer", "Archer Enemy"),
    ("spawn_tanker", "Tanker Enemy"),
    ("reset_hp", "Reset Player HP"),
    ("reset_map", "Reset Map"),
    ("toggle_attack_ranges", "Attack Ranges: OFF"),
    ("toggle_hitboxes", "Hitboxes: OFF"),
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
        enemy_images=None,
        enemy_draw_rectangle=None,
        enemy_draw_circle=None,
        arrow_image=None,
    ):
        self.player = player
        self.gun = gun
        self.background = background
        self.camera = camera or Camera()
        self.gun_image = gun_image
        self.bullet_image = bullet_image
        self.hud_font = hud_font
        self.enemy_images = dict(enemy_images or {})
        self.enemy_draw_rectangle = enemy_draw_rectangle
        self.enemy_draw_circle = enemy_draw_circle
        self.arrow_image = arrow_image
        self.initial_player_position = (player.x, player.y)
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.mouse_held = False
        self._mouse_pressed = False
        self.debug_mode = False
        self.show_attack_ranges = False
        self.show_hitboxes = False

        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()

    def close(self):
        game_world.clear()

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

    def spawn_test_enemies(self):
        offsets = {
            EnemyType.BASIC: (-220, 0),
            EnemyType.EXPLOSIVE: (220, 0),
            EnemyType.TANKER: (0, 220),
            EnemyType.ASSASSIN: (0, -220),
            EnemyType.ARCHER: (220, 220),
        }
        return tuple(
            self.spawn_enemy(
                enemy_type,
                self.player.x + offset_x,
                self.player.y + offset_y,
            )
            for enemy_type, (offset_x, offset_y) in offsets.items()
        )

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key == "f1":
            self.debug_mode = not self.debug_mode
            self.gun.infinite_ammo = self.debug_mode
        elif key == "e":
            self.gun.toggle_mode()
        elif key == "r":
            self.gun.start_reload()

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
        return DEBUG_MENU_LEFT + 8, top, SCREEN_WIDTH - 8, top + DEBUG_BUTTON_HEIGHT

    def _handle_debug_click(self, screen_x, screen_y):
        menu_bottom = DEBUG_BUTTON_TOP + len(DEBUG_MENU_ITEMS) * DEBUG_BUTTON_SPACING
        if not (
            DEBUG_MENU_LEFT <= screen_x <= SCREEN_WIDTH - 8
            and 8 <= screen_y <= menu_bottom
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
        elif action == "reset_map":
            self.reset_map()
        elif action == "toggle_attack_ranges":
            self.show_attack_ranges = not self.show_attack_ranges
        elif action == "toggle_hitboxes":
            self.show_hitboxes = not self.show_hitboxes

    def reset_map(self):
        self.player.x, self.player.y = self.initial_player_position
        self.player.hp = self.player.max_hp
        self.player.aim_angle = 0.0
        self.player.set_movement(0, 0, 0.0)
        self.gun.reset()
        self.gun.infinite_ammo = self.debug_mode
        self.keys.clear()
        self.mouse_held = False
        self._mouse_pressed = False
        self.show_attack_ranges = False
        self.show_hitboxes = False
        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()
        self.spawn_test_enemies()

    def update(self, delta_time):
        self.gun.update(delta_time)
        move_x = int("d" in self.keys) - int("a" in self.keys)
        move_y = int("w" in self.keys) - int("s" in self.keys)
        self.player.set_movement(move_x, move_y, delta_time)
        game_world.update()

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
                muzzle_offset = PLAYER_RADIUS + 14
                game_world.add_object(
                    Bullet(
                        self.player.x
                        + math.cos(self.player.aim_angle) * muzzle_offset,
                        self.player.y
                        + math.sin(self.player.aim_angle) * muzzle_offset,
                        self.player.aim_angle,
                        self.bullet_image,
                        damage=self.gun.spec.damage,
                    ),
                    depth=2,
                )
        self._remove_defeated_enemies()

    def _remove_defeated_enemies(self):
        defeated = [
            obj
            for layer in game_world.world
            for obj in tuple(layer)
            if isinstance(obj, Enemy) and not obj.is_alive
        ]
        for enemy in defeated:
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
        game_world.render()
        if self.show_attack_ranges or self.show_hitboxes:
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
                42,
                24,
            )
        if self.hud_font is None:
            raise RuntimeError("BattleScene.draw requires a loaded HUD font")
        draw_hud(
            self.player,
            self.gun,
            self.hud_font,
            draw_rectangle,
        )
        if self.debug_mode:
            self._draw_debug_menu(draw_rectangle)

    def _debug_menu_items(self):
        return tuple(
            (
                action,
                label.replace(
                    "OFF",
                    "ON"
                    if (
                        self.show_attack_ranges
                        if action == "toggle_attack_ranges"
                        else self.show_hitboxes
                    )
                    else "OFF",
                )
                if action in ("toggle_attack_ranges", "toggle_hitboxes")
                else label,
            )
            for action, label in DEBUG_MENU_ITEMS
        )

    def _draw_debug_menu(self, draw_rectangle):
        menu_bottom = DEBUG_BUTTON_TOP + len(DEBUG_MENU_ITEMS) * DEBUG_BUTTON_SPACING
        draw_rectangle(
            DEBUG_MENU_LEFT,
            SCREEN_HEIGHT - menu_bottom - 8,
            SCREEN_WIDTH - 8,
            SCREEN_HEIGHT - 8,
            25,
            30,
            40,
            230,
            True,
        )
        self.hud_font.draw(
            DEBUG_MENU_LEFT + 8,
            SCREEN_HEIGHT - 30,
            "DEBUG MODE",
            (255, 220, 80),
        )
        for index, (_, label) in enumerate(self._debug_menu_items()):
            left, top, right, bottom = self._debug_button_bounds(index)
            self.hud_font.draw(
                left + 6,
                SCREEN_HEIGHT - bottom + 6,
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
