"""First-stage battle scene: movement, aiming, pistol controls, and HUD."""

import game_world
from game_camera import Camera
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import draw_hud
from player import Player
from shot_result import HitResult
from weapon import Gun


class BattleScene:
    def __init__(self, player, gun, background, camera=None):
        self.player = player
        self.gun = gun
        self.background = background
        self.camera = camera or Camera()
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.mouse_held = False
        self._mouse_pressed = False
        self.last_shot_result = None
        self.result_display_time = 0.0

        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()

    def close(self):
        game_world.clear()

    def key_down(self, key):
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key == "e":
            self.gun.toggle_mode()
        elif key == "r":
            self.gun.start_reload()

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y

    def mouse_down(self, button):
        if button == "left" and not self.mouse_held:
            self.mouse_held = True
            self._mouse_pressed = True

    def mouse_up(self, button):
        if button == "left":
            self.mouse_held = False

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
            self.last_shot_result = HitResult.MISS
            self.result_display_time = 1.0
        else:
            self.result_display_time = max(0.0, self.result_display_time - delta_time)
            if self.result_display_time == 0:
                self.last_shot_result = None

    def _update_player_view(self):
        screen_x, screen_y = self.camera.world_to_screen(self.player.x, self.player.y)
        self.player.set_screen_position(screen_x, screen_y)

    def draw(self, draw_line, set_color):
        first_column = int(self.camera.x // SCREEN_WIDTH)
        last_column = int((self.camera.x + SCREEN_WIDTH) // SCREEN_WIDTH)
        first_row = int(self.camera.y // SCREEN_HEIGHT)
        last_row = int((self.camera.y + SCREEN_HEIGHT) // SCREEN_HEIGHT)

        for row in range(first_row, last_row + 1):
            for column in range(first_column, last_column + 1):
                screen_x = column * SCREEN_WIDTH - self.camera.x + SCREEN_WIDTH / 2
                screen_y = row * SCREEN_HEIGHT - self.camera.y + SCREEN_HEIGHT / 2
                self.background.draw(screen_x, screen_y, SCREEN_WIDTH, SCREEN_HEIGHT)

        game_world.render()
        set_color(245, 220, 120)
        target_x = self.mouse_screen_x
        target_y = SCREEN_HEIGHT - self.mouse_screen_y
        draw_line(
            self.player.screen_position[0],
            self.player.screen_position[1],
            target_x,
            target_y,
        )
        result_text = None
        if self.last_shot_result is not None and self.result_display_time > 0:
            result_text = "SHOT {}".format(self.last_shot_result.value.upper())
        draw_hud(self.player, self.gun, result_text, draw_line, set_color)
