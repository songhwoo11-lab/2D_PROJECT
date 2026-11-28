"""First-stage battle scene: movement, aiming, pistol controls, and HUD."""

from enum import Enum
import math
import random

import pico2d

from arrow import Arrow
from audio import (
    BATTLE_MUSIC_FILE,
    BATTLE_PORTAL_EXIT_SOUND_FILE,
    DEFEAT_MUSIC_FILE,
    MACHINE_GUN_SHOT_SOUND_FILE,
    OVERHEAT_SOUND_FILE,
    PISTOL_SHOT_SOUND_FILE,
    RELOAD_SOUND_FILE,
    RIFLE_SHOT_SOUND_FILE,
    VICTORY_MUSIC_FILE,
)
import battle_record
from bullet import Bullet
from enemy import (
    DAMAGE_SOURCE_EXPLOSION,
    ENEMY_STATS,
    Enemy,
    EnemyType,
)
from enemy_types import AssassinEnemy, create_enemy
import game_world
from game_camera import Camera
from game_config import (
    AIM_CURSOR_ALPHA,
    AIM_CURSOR_COLOR,
    AIM_CURSOR_GAP,
    AIM_CURSOR_RADIUS,
    AIM_CURSOR_THICKNESS,
    COOLING_DROP_CHANCE,
    COOLING_PICKUP_LIMIT,
    HEALTH_PICKUP_LIMIT,
    MAGAZINE_PICKUP_AMMO,
    PICKUP_DRAW_SIZE,
    PLAYER_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from hud import draw_centered_text, draw_hud
from player import Player
from pickup import (
    CoolingPickup,
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
from weapon import (
    DEFAULT_GUN_ID,
    Gun,
    MACHINE_GUN_GUN_ID,
    RIFLE_GUN_ID,
)


SHOT_FEEDBACK_DURATION = 0.8
SHOT_FEEDBACK_COLOR = (255, 255, 255)
SHOT_FEEDBACK_FONT_SIZE = 48
WAVE_BANNER_SECONDS = 2.5
WAVE_STRENGTH_BANNER_SECONDS = 3.5
BATTLE_START_COUNTDOWN_SECONDS = 3.0
BATTLE_PORTAL_EXIT_SECONDS = 3.0
BATTLE_PORTAL_EXIT_ROTATIONS = 3.0
BATTLE_PORTAL_EXIT_MOVE_DISTANCE = 360.0
BATTLE_PORTAL_EXIT_SPEED_DECAY_RATE = 3.0
BATTLE_PORTAL_FADE_SECONDS = 1.0
BATTLE_PORTAL_CAMERA_PAN_SECONDS = 0.8
BATTLE_PORTAL_IMAGE_WIDTH = 700
BATTLE_PORTAL_IMAGE_HEIGHT = 660

# 총 온도가 한계 온도의 이 비율에 도달하는 시점부터 서서히 붉게 물든다.
GUN_HEAT_TINT_START_RATIO = 0.5
# 한계 온도에 가까워질수록 이 색조에 가까워진다.
GUN_HEAT_TINT_COLOR = (255, 80, 80)
# 과열 상태(사격 차단 중)에서 적용하는 색조
GUN_OVERHEAT_TINT = (80, 140, 255)
# 색조가 없는 기본 상태 및 그리기 후 복원 값
GUN_WHITE_TINT = (255, 255, 255)

# 발사 반동 애니메이션: 발사 순간 총구 반대 방향으로 밀렸다가 복귀한다.
GUN_RECOIL_DISTANCE = 18.0
GUN_RECOIL_RECOVERY_SECONDS = 0.18
GUN_PIVOT_Y_OFFSETS = {
    DEFAULT_GUN_ID: 0.0,
    RIFLE_GUN_ID: 10.0,
    MACHINE_GUN_GUN_ID: 20.0,
}
GUN_PIVOT_LEFT_OFFSETS = {
    DEFAULT_GUN_ID: 0.0,
    RIFLE_GUN_ID: 0.0,
    MACHINE_GUN_GUN_ID: 0.0,
}
SHOT_SOUND_BY_GUN_ID = {
    DEFAULT_GUN_ID: PISTOL_SHOT_SOUND_FILE,
    RIFLE_GUN_ID: RIFLE_SHOT_SOUND_FILE,
    MACHINE_GUN_GUN_ID: MACHINE_GUN_SHOT_SOUND_FILE,
}

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
DEBUG_MENU_WIDTH = 380
DEBUG_MENU_LEFT = SCREEN_WIDTH - DEBUG_MENU_WIDTH - 16
DEBUG_BUTTON_TOP = 84
DEBUG_BUTTON_HEIGHT = 52
DEBUG_BUTTON_SPACING = 60
DEBUG_BUTTON_TEXT_Y_OFFSET = 10
DEBUG_FONT_SIZE = 30
DEBUG_COIN_AMOUNT = 10000
DEBUG_ADD_COINS_LABEL = "+10000 Coins"
DEBUG_MENU_ITEMS = (
    ("spawn_basic", "Basic Enemy"),
    ("spawn_explosive", "Explosive Enemy"),
    ("spawn_assassin", "Assassin Enemy"),
    ("spawn_archer", "Archer Enemy"),
    ("spawn_tanker", "Tanker Enemy"),
    ("remove_all_enemies", "Remove All Enemies"),
    ("reset_hp", "Reset Player HP"),
    ("reset_map", "Reset Map"),
    ("add_coins", DEBUG_ADD_COINS_LABEL),
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
        cooling_image=None,
        random_source=None,
        total_waves=None,
        wave_spawn_rate=None,
        gun_images=None,
        portal_image=None,
        portal_transition=False,
        audio=None,
    ):
        self.player = player
        self.gun = gun
        self.background = background
        self.camera = camera or Camera()
        self.gun_image = gun_image
        self.gun_images = dict(gun_images or {})
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
        self.cooling_image = cooling_image
        self.portal_image = portal_image
        self.audio = audio
        self._wave_music_started = False
        self.initial_player_position = (player.x, player.y)
        self.portal_transition_active = bool(portal_transition)
        self.portal_transition_elapsed = 0.0
        self.portal_fade_active = False
        self.portal_fade_elapsed = 0.0
        self.portal_camera_pan_active = False
        self.portal_camera_pan_elapsed = 0.0
        self.portal_camera_pan_start = (0.0, 0.0)
        self.portal_camera_pan_end = (0.0, 0.0)
        self.portal_transition_angle = 0.0
        self.portal_transition_opacity = 1.0
        self.portal_transition_scale = 1.0
        self.portal_transition_start_position = self.initial_player_position
        self.portal_transition_end_position = (
            self.initial_player_position[0],
            max(
                PLAYER_RADIUS,
                self.initial_player_position[1]
                - BATTLE_PORTAL_EXIT_MOVE_DISTANCE,
            ),
        )
        self.keys = set()
        self.mouse_screen_x = SCREEN_WIDTH / 2
        self.mouse_screen_y = SCREEN_HEIGHT / 2
        self.mouse_held = False
        self._mouse_pressed = False
        self.gun_recoil_remaining = 0.0
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
        self.start_countdown_remaining = BATTLE_START_COUNTDOWN_SECONDS
        self.waves_cleared = False
        self.elapsed_time = 0.0
        self.reached_wave = 1
        self.clear_time = None
        self.coins = 0
        self.pickups = []
        self.health_pickups = []
        self.cooling_pickups = []
        self.paused = False
        self.pause_menu_index = 0
        self.finished = False
        self.result = None
        self.exit_requested = False

        if self.portal_transition_active:
            self.player.x, self.player.y = self.portal_transition_start_position
            self._set_portal_player_transform(0.0)
        game_world.clear()
        game_world.add_object(self.player, depth=1)
        if self.portal_transition_active:
            self.camera.follow(*self.initial_player_position)
        else:
            self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()
        if self.portal_transition_active:
            self._play_portal_exit_sound()
        self._start_battle_music()

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

    def _start_battle_music(self):
        if self.audio is None or self._wave_music_started:
            return
        if self.finished or self.paused or self.portal_transition_active:
            return
        self._wave_music_started = True
        self.audio.play(BATTLE_MUSIC_FILE)

    def _stop_battle_music(self):
        if self.audio is None or not self._wave_music_started:
            return
        self._wave_music_started = False
        self.audio.stop()

    def _play_result_music(self, name):
        if self.audio is None:
            return
        play_once = getattr(self.audio, "play_once", None)
        if play_once is not None:
            play_once(name)

    def _play_shot_sound(self):
        if self.audio is None:
            return
        sound_file = SHOT_SOUND_BY_GUN_ID.get(getattr(self.gun, "gun_id", None))
        if sound_file is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            play_sound(sound_file)

    def _play_reload_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            play_sound(RELOAD_SOUND_FILE, target_duration=self.gun.reload_seconds)

    def _play_overheat_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            play_sound(OVERHEAT_SOUND_FILE)

    def _play_portal_exit_sound(self):
        if self.audio is None:
            return
        play_sound = getattr(self.audio, "play_sound", None)
        if play_sound is not None:
            play_sound(BATTLE_PORTAL_EXIT_SOUND_FILE)

    def _pause_reload_sound(self):
        self._control_reload_sound("pause_sound")

    def _resume_reload_sound(self):
        self._control_reload_sound("resume_sound")

    def _stop_reload_sound(self):
        self._control_reload_sound("stop_sound")

    def _control_reload_sound(self, method_name):
        if self.audio is None:
            return
        control = getattr(self.audio, method_name, None)
        if control is not None:
            control(RELOAD_SOUND_FILE)

    def _start_reload(self):
        self.gun.start_reload(self._play_reload_sound)

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

    @property
    def is_counting_down(self):
        return (
            not self.portal_transition_active
            and self.start_countdown_remaining > 0.0
        )

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
        if getattr(enemy, "last_damage_source", None) == DAMAGE_SOURCE_EXPLOSION:
            return
        if self._drop_health_pickup(enemy):
            return
        if self._drop_cooling_pickup(enemy):
            return
        if roll_magazine_drop(self.gun.total_ammo, self.random_source):
            self.pickups.append(
                MagazinePickup(
                    enemy.x,
                    enemy.y,
                    self._magazine_pickup_amount(),
                    image=self.ammo_image,
                    phase=self._pickup_bob_phase(),
                )
            )

    def _drop_health_pickup(self, enemy):
        """Drop a health potion. Returns True when it was dropped."""
        if len(self.health_pickups) >= HEALTH_PICKUP_LIMIT:
            return False
        if not roll_health_drop(
            self.player.hp,
            self.player.max_hp,
            self.random_source,
        ):
            return False
        self.health_pickups.append(
            HealthPickup(
                enemy.x,
                enemy.y,
                image=self.health_image,
                phase=self._pickup_bob_phase(),
            )
        )
        return True

    def _drop_cooling_pickup(self, enemy):
        """Drop a cooling item. Returns True when it was dropped."""
        if len(self.cooling_pickups) >= COOLING_PICKUP_LIMIT:
            return False
        if self.random_source.random() >= COOLING_DROP_CHANCE:
            return False
        self.cooling_pickups.append(
            CoolingPickup(
                enemy.x,
                enemy.y,
                image=self.cooling_image,
                phase=self._pickup_bob_phase(),
            )
        )
        return True

    def _pickup_bob_phase(self):
        return self.random_source.uniform(0.0, 2.0 * math.pi)

    def _update_pickups(self, delta_time):
        remaining = []
        for pickup in self.pickups:
            pickup.update(delta_time)
            if pickup.can_collect(self.player):
                if self.gun.add_reserve_ammo(pickup.amount) > 0:
                    continue
            remaining.append(pickup)
        self.pickups = remaining
        remaining_health = []
        for pickup in self.health_pickups:
            pickup.update(delta_time)
            if pickup.can_collect(self.player):
                if self.player.heal(pickup.amount) > 0:
                    continue
            remaining_health.append(pickup)
        self.health_pickups = remaining_health
        remaining_cooling = []
        for pickup in self.cooling_pickups:
            pickup.update(delta_time)
            if pickup.can_collect(self.player):
                if self.gun.apply_cooling_item():
                    continue
            remaining_cooling.append(pickup)
        self.cooling_pickups = remaining_cooling

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
        if self.portal_transition_active:
            return
        key = key.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.finished:
            if key == "space":
                self.exit_requested = True
            return
        if key == "escape":
            if self.is_counting_down:
                return
            self.paused = not self.paused
            if self.paused:
                self.pause_menu_index = 0
                self._stop_battle_music()
                self._pause_reload_sound()
            else:
                self._start_battle_music()
                self._resume_reload_sound()
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
            elif key == "space":
                self._select_pause_menu_item()
            return
        if key == "f1":
            self.debug_mode = not self.debug_mode
            self.gun.infinite_ammo = self.debug_mode
            self.gun.heat_enabled = not self.debug_mode
        elif key == "e":
            self.gun.toggle_mode()
        elif key == "r":
            self._start_reload()

    def _select_pause_menu_item(self):
        if self.pause_menu_index == 0:
            self.paused = False
            self._start_battle_music()
            self._resume_reload_sound()
        else:
            self._finish(BattleResult.QUIT)

    def _finish(self, result):
        if self.finished:
            return
        self.finished = True
        self.result = result
        self.paused = False
        self._stop_battle_music()
        self._stop_reload_sound()
        if result is BattleResult.DEFEAT:
            self._play_result_music(DEFEAT_MUSIC_FILE)
        elif result is BattleResult.VICTORY:
            self._play_result_music(VICTORY_MUSIC_FILE)
            self.clear_time = self.elapsed_time

    def key_up(self, key):
        self.keys.discard(key.lower())

    def mouse_move(self, screen_x, screen_y):
        self.mouse_screen_x = screen_x
        self.mouse_screen_y = screen_y
        if self.paused and not self.finished:
            hovered = self._pause_menu_item_at(screen_x, screen_y)
            if hovered is not None:
                self.pause_menu_index = hovered

    def _pause_menu_item_at(self, screen_x, screen_y):
        """Return the pause menu item under the given screen position."""
        canvas_y = SCREEN_HEIGHT - screen_y
        center_x = SCREEN_WIDTH / 2
        for index, _label in enumerate(PAUSE_MENU_ITEMS):
            item_y = SCREEN_HEIGHT / 2 + 24 - index * 68
            if (
                abs(screen_x - center_x) <= 220
                and abs(canvas_y - item_y) <= 34
            ):
                return index
        return None

    @property
    def aim_cursor_position(self):
        """Cursor position in canvas coordinates (origin at the bottom-left)."""
        return self.mouse_screen_x, SCREEN_HEIGHT - self.mouse_screen_y

    @property
    def shows_aim_cursor(self):
        return (
            not self.portal_transition_active
            and not self.paused
            and not self.finished
        )

    @property
    def shows_system_cursor(self):
        if not self.shows_aim_cursor:
            return True
        return self.debug_mode and self._debug_menu_contains(
            self.mouse_screen_x,
            self.mouse_screen_y,
        )

    def mouse_down(self, button, screen_x=None, screen_y=None):
        if self.portal_transition_active:
            return
        if (
            button == "left"
            and self.paused
            and not self.finished
            and screen_x is not None
            and screen_y is not None
        ):
            hovered = self._pause_menu_item_at(screen_x, screen_y)
            if hovered is not None:
                self.pause_menu_index = hovered
                self._select_pause_menu_item()
                return
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
            DEBUG_MENU_LEFT + 16,
            top,
            SCREEN_WIDTH - 16,
            top + DEBUG_BUTTON_HEIGHT,
        )

    def _debug_menu_contains(self, screen_x, screen_y):
        if screen_x is None or screen_y is None:
            return False
        menu_bottom = DEBUG_BUTTON_TOP + len(DEBUG_MENU_ITEMS) * DEBUG_BUTTON_SPACING
        return (
            DEBUG_MENU_LEFT <= screen_x <= SCREEN_WIDTH - 16
            and 16 <= screen_y <= menu_bottom
        )

    def _handle_debug_click(self, screen_x, screen_y):
        if not self._debug_menu_contains(screen_x, screen_y):
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
        elif action == "add_coins":
            self.coins += DEBUG_COIN_AMOUNT
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
        self._stop_battle_music()
        self._stop_reload_sound()
        self.portal_transition_active = False
        self.portal_transition_elapsed = 0.0
        self.portal_fade_active = False
        self.portal_fade_elapsed = 0.0
        self.portal_camera_pan_active = False
        self.portal_camera_pan_elapsed = 0.0
        self.portal_transition_angle = 0.0
        self.portal_transition_opacity = 1.0
        self.portal_transition_scale = 1.0
        self.player.reset_render_transform()
        self.player.x, self.player.y = self.initial_player_position
        self.player.hp = self.player.max_hp
        self.player.reset_hp_trail()
        self.player.aim_angle = 0.0
        self.player.set_movement(0, 0)
        self.gun.reset()
        self.gun.infinite_ammo = self.debug_mode
        self.gun.heat_enabled = not self.debug_mode
        self.keys.clear()
        self.mouse_held = False
        self._mouse_pressed = False
        self.gun_recoil_remaining = 0.0
        self.show_attack_ranges = False
        self.show_hitboxes = False
        self.show_assassin_reveal_range = False
        self.wave_director = self._create_wave_director()
        self.spawn_warnings = []
        self.wave_banner_text = ""
        self.wave_banner_remaining = 0.0
        self.start_countdown_remaining = BATTLE_START_COUNTDOWN_SECONDS
        self.waves_cleared = False
        self.elapsed_time = 0.0
        self.reached_wave = 1
        self.clear_time = None
        self.coins = 0
        self.pickups = []
        self.health_pickups = []
        self.cooling_pickups = []
        self.paused = False
        self.pause_menu_index = 0
        self.finished = False
        self.result = None
        self.exit_requested = False
        game_world.clear()
        game_world.add_object(self.player, depth=1)
        self.camera.follow(self.player.x, self.player.y)
        self._update_player_view()
        self._start_battle_music()

    def _set_portal_player_transform(self, progress):
        self.portal_transition_angle = (
            math.tau * BATTLE_PORTAL_EXIT_ROTATIONS * progress
        )
        self.portal_transition_opacity = progress
        self.portal_transition_scale = progress
        self.player.render_angle = self.portal_transition_angle
        self.player.render_opacity = self.portal_transition_opacity
        self.player.render_scale = self.portal_transition_scale

    @staticmethod
    def _portal_transition_progress(elapsed):
        linear_progress = min(
            max(elapsed / BATTLE_PORTAL_EXIT_SECONDS, 0.0),
            1.0,
        )
        remaining = 1.0 - linear_progress
        decay = (
            math.exp(BATTLE_PORTAL_EXIT_SPEED_DECAY_RATE * remaining) - 1.0
        ) / (math.exp(BATTLE_PORTAL_EXIT_SPEED_DECAY_RATE) - 1.0)
        return 1.0 - decay

    def _portal_gun_reverse_angle(self):
        return -(
            BATTLE_PORTAL_EXIT_ROTATIONS * math.tau
            - self.portal_transition_angle
        )

    def _portal_gun_screen_offset(self):
        aim_angle = self.player.aim_angle
        final_x = (
            math.cos(aim_angle) * PLAYER_RADIUS * 0.6
            - self._gun_pivot_left_offset()
        )
        final_y = (
            math.sin(aim_angle) * PLAYER_RADIUS * 0.6
            - self._gun_pivot_y_offset()
        )
        reverse_angle = self._portal_gun_reverse_angle()
        cosine = math.cos(reverse_angle)
        sine = math.sin(reverse_angle)
        return (
            (final_x * cosine - final_y * sine) * self.portal_transition_scale,
            (final_x * sine + final_y * cosine) * self.portal_transition_scale,
        )

    def _camera_offset_for_position(self, world_x, world_y):
        max_x = max(self.camera.world_width - self.camera.screen_width, 0.0)
        max_y = max(self.camera.world_height - self.camera.screen_height, 0.0)
        return (
            min(max(world_x - self.camera.screen_width / 2, 0.0), max_x),
            min(max(world_y - self.camera.screen_height / 2, 0.0), max_y),
        )

    def _update_portal_fade(self, delta_time):
        self.portal_fade_elapsed = min(
            BATTLE_PORTAL_FADE_SECONDS,
            self.portal_fade_elapsed + delta_time,
        )
        self.camera.follow(*self.portal_transition_start_position)
        self._update_player_view()
        if self.portal_fade_elapsed < BATTLE_PORTAL_FADE_SECONDS:
            return
        self.portal_fade_active = False
        self.portal_camera_pan_active = True
        self.portal_camera_pan_elapsed = 0.0
        self.portal_camera_pan_start = (self.camera.x, self.camera.y)
        self.portal_camera_pan_end = self._camera_offset_for_position(
            *self.portal_transition_end_position
        )

    def _update_portal_camera_pan(self, delta_time):
        self.portal_camera_pan_elapsed = min(
            BATTLE_PORTAL_CAMERA_PAN_SECONDS,
            self.portal_camera_pan_elapsed + delta_time,
        )
        linear_progress = min(
            max(self.portal_camera_pan_elapsed / BATTLE_PORTAL_CAMERA_PAN_SECONDS, 0.0),
            1.0,
        )
        progress = linear_progress * linear_progress * (3.0 - 2.0 * linear_progress)
        start_x, start_y = self.portal_camera_pan_start
        end_x, end_y = self.portal_camera_pan_end
        self.camera.x = start_x + (end_x - start_x) * progress
        self.camera.y = start_y + (end_y - start_y) * progress
        self._update_player_view()
        if self.portal_camera_pan_elapsed < BATTLE_PORTAL_CAMERA_PAN_SECONDS:
            return
        self.camera.follow(*self.portal_transition_end_position)
        self._update_player_view()
        self.portal_camera_pan_active = False
        self.portal_transition_active = False
        self.start_countdown_remaining = BATTLE_START_COUNTDOWN_SECONDS
        self._start_battle_music()

    def _update_portal_transition(self, delta_time):
        if self.portal_camera_pan_active:
            self._update_portal_camera_pan(delta_time)
            return
        if self.portal_fade_active:
            self._update_portal_fade(delta_time)
            return
        self.portal_transition_elapsed = min(
            BATTLE_PORTAL_EXIT_SECONDS,
            self.portal_transition_elapsed + delta_time,
        )
        progress = self._portal_transition_progress(self.portal_transition_elapsed)
        start_x, start_y = self.portal_transition_start_position
        end_x, end_y = self.portal_transition_end_position
        self.player.x = start_x + (end_x - start_x) * progress
        self.player.y = start_y + (end_y - start_y) * progress
        self._set_portal_player_transform(progress)
        self.camera.follow(*self.portal_transition_start_position)
        self._update_player_view()
        if self.portal_transition_elapsed < BATTLE_PORTAL_EXIT_SECONDS:
            return
        self.player.x, self.player.y = self.portal_transition_end_position
        self.player.reset_render_transform()
        self.portal_transition_angle = 0.0
        self.portal_transition_opacity = 1.0
        self.portal_transition_scale = 1.0
        self.portal_fade_active = True
        self.portal_fade_elapsed = 0.0

    def update(self, delta_time):
        if self.finished or self.paused:
            return
        if self.portal_transition_active:
            self._stop_battle_music()
            self._update_portal_transition(delta_time)
            return
        if self.is_counting_down:
            self.start_countdown_remaining = max(
                0.0,
                self.start_countdown_remaining - delta_time,
            )
            if not self.is_counting_down:
                self._announce_wave()
        else:
            self.elapsed_time += delta_time
        self.shot_feedbacks = [
            (x, y, label, remaining - delta_time)
            for x, y, label, remaining in self.shot_feedbacks
            if remaining > delta_time
        ]
        self.gun.update(delta_time)
        self._update_gun_recoil(delta_time)
        move_x = int("d" in self.keys) - int("a" in self.keys)
        move_y = int("w" in self.keys) - int("s" in self.keys)
        self.player.set_movement(move_x, move_y)
        bullets = [
            obj
            for layer in game_world.world
            for obj in layer
            if isinstance(obj, Bullet)
        ]
        game_world.update(delta_time)
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

        fired = False
        if not self.is_counting_down:
            fired = self.gun.handle_fire_input(
                mouse_held=self.mouse_held,
                mouse_pressed=self._mouse_pressed,
                on_reload_started=self._play_reload_sound,
                on_overheated=self._play_overheat_sound,
            )
        self._mouse_pressed = False
        if fired:
            self.gun_recoil_remaining = GUN_RECOIL_RECOVERY_SECONDS
            self._play_shot_sound()
            if self.bullet_image is not None:
                muzzle_offset = PLAYER_RADIUS + 28
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
        self._update_pickups(delta_time)
        if not self.is_counting_down:
            self._update_waves(delta_time)
        self.wave_banner_remaining = max(
            0.0,
            self.wave_banner_remaining - delta_time,
        )
        if self.waves_cleared:
            self._finish(BattleResult.VICTORY)

    def _update_gun_recoil(self, delta_time):
        if self.gun_recoil_remaining <= 0.0:
            return
        self.gun_recoil_remaining = max(
            0.0,
            self.gun_recoil_remaining - delta_time,
        )

    def _gun_recoil_offset(self):
        """Return how far the gun is currently pushed back from its rest pose."""
        if self.gun_recoil_remaining <= 0.0:
            return 0.0
        progress = self.gun_recoil_remaining / GUN_RECOIL_RECOVERY_SECONDS
        progress = min(max(progress, 0.0), 1.0)
        return GUN_RECOIL_DISTANCE * progress * progress

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
                    target.y + target.radius + 8,
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
        background_x, background_y = self.camera.world_to_screen(
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
        )
        self.background.draw(
            background_x,
            background_y,
            WORLD_WIDTH,
            WORLD_HEIGHT,
        )
        if self.portal_transition_active:
            if self.portal_image is not None and not self.portal_camera_pan_active:
                portal_opacity = 1.0
                if self.portal_fade_active:
                    portal_opacity = 1.0 - min(
                        max(self.portal_fade_elapsed / BATTLE_PORTAL_FADE_SECONDS, 0.0),
                        1.0,
                    )
                opacify = getattr(self.portal_image, "opacify", None)
                if portal_opacity < 1.0 and opacify is not None:
                    opacify(portal_opacity)
                    try:
                        self.portal_image.draw(
                            SCREEN_WIDTH / 2,
                            SCREEN_HEIGHT / 2,
                            BATTLE_PORTAL_IMAGE_WIDTH,
                            BATTLE_PORTAL_IMAGE_HEIGHT,
                        )
                    finally:
                        opacify(1.0)
                else:
                    self.portal_image.draw(
                        SCREEN_WIDTH / 2,
                        SCREEN_HEIGHT / 2,
                        BATTLE_PORTAL_IMAGE_WIDTH,
                        BATTLE_PORTAL_IMAGE_HEIGHT,
                    )
            game_world.render(self._is_visible_on_screen)
            if self._selected_gun_image() is not None:
                if self.portal_fade_active or self.portal_camera_pan_active:
                    self._draw_gun()
                else:
                    self._draw_gun(
                        angle=self._portal_gun_reverse_angle(),
                        opacity=self.portal_transition_opacity,
                        scale=self.portal_transition_scale,
                        allow_flip=False,
                        screen_offset=self._portal_gun_screen_offset(),
                    )
            return

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
        if self.shows_aim_cursor:
            self._draw_aim_cursor(draw_rectangle)
        if (
            self.show_attack_ranges
            or self.show_hitboxes
            or self.show_assassin_reveal_range
        ):
            self._draw_enemy_debug_circles()
        if self._selected_gun_image() is not None:
            self._draw_gun()
        if self.hud_font is None:
            raise RuntimeError("BattleScene.draw requires a loaded HUD font")
        self._draw_wave_banner()
        if self.is_counting_down:
            draw_centered_text(
                self.hud_font,
                SCREEN_HEIGHT * 3 / 4,
                str(math.ceil(self.start_countdown_remaining)),
                (255, 220, 100),
            )
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

    def _selected_gun_image(self):
        gun_id = getattr(self.gun, "gun_id", None)
        return self.gun_images.get(gun_id, self.gun_image)

    def _gun_pivot_left_offset(self):
        gun_id = getattr(self.gun, "gun_id", None)
        return GUN_PIVOT_LEFT_OFFSETS.get(gun_id, 0.0)

    def _gun_pivot_y_offset(self):
        gun_id = getattr(self.gun, "gun_id", None)
        return GUN_PIVOT_Y_OFFSETS.get(gun_id, 0.0)

    def _draw_gun(
        self,
        angle=None,
        opacity=None,
        scale=1.0,
        allow_flip=True,
        screen_offset=None,
    ):
        """Draw the gun with its recoil offset and temperature tint."""
        image = self._selected_gun_image()
        aim_angle = self.player.aim_angle if angle is None else angle
        if screen_offset is None:
            gun_offset = PLAYER_RADIUS * 0.6 * scale
            recoil_offset = self._gun_recoil_offset()
            gun_x = (
                self.player.screen_position[0]
                + math.cos(aim_angle) * gun_offset
                - math.cos(aim_angle) * recoil_offset
                - self._gun_pivot_left_offset() * scale
            )
            gun_y = (
                self.player.screen_position[1]
                + math.sin(aim_angle) * gun_offset
                - math.sin(aim_angle) * recoil_offset
                - self._gun_pivot_y_offset() * scale
            )
        else:
            gun_x = self.player.screen_position[0] + screen_offset[0]
            gun_y = self.player.screen_position[1] + screen_offset[1]
        gun_angle = aim_angle
        flip = ""
        if allow_flip:
            if gun_angle > math.pi / 2:
                gun_angle -= math.pi
                flip = "h"
            elif gun_angle < -math.pi / 2:
                gun_angle += math.pi
                flip = "h"

        texture = getattr(image, "texture", None)
        if texture is not None:
            pico2d.SDL_SetTextureColorMod(texture, *self._gun_tint_color())
        opacify = (
            getattr(image, "opacify", None)
            if opacity is not None and opacity < 1.0
            else None
        )
        if opacify is not None:
            opacify(opacity)
        try:
            image.composite_draw(
                gun_angle,
                flip,
                gun_x,
                gun_y,
                126 * scale,
                72 * scale,
            )
        finally:
            if texture is not None:
                pico2d.SDL_SetTextureColorMod(texture, *GUN_WHITE_TINT)
            if opacify is not None:
                opacify(1.0)

    def _gun_tint_color(self):
        """Return the gun tint for the current temperature.

        Overheating always uses blue. Otherwise the sprite reddens gradually
        from ``GUN_HEAT_TINT_START_RATIO`` of the temperature limit.
        """
        if self.gun.overheated:
            return GUN_OVERHEAT_TINT
        start_temperature = (
            self.gun.temperature_limit * GUN_HEAT_TINT_START_RATIO
        )
        if self.gun.temperature <= start_temperature:
            return GUN_WHITE_TINT
        progress = (self.gun.temperature - start_temperature) / (
            self.gun.temperature_limit - start_temperature
        )
        progress = min(max(progress, 0.0), 1.0)
        return tuple(
            round(255 + (component - 255) * progress)
            for component in GUN_HEAT_TINT_COLOR
        )

    def _draw_spawn_warnings(self):
        if self.enemy_draw_circle is None:
            return
        for warning, _, _, _ in self.spawn_warnings:
            screen_x, screen_y = self.camera.world_to_screen(
                warning.x,
                warning.y,
            )
            margin = warning.radius + 40
            if not (
                -margin <= screen_x <= SCREEN_WIDTH + margin
                and -margin <= screen_y <= SCREEN_HEIGHT + margin
            ):
                continue
            self.enemy_draw_circle(
                screen_x,
                screen_y,
                round(warning.radius + 12 * warning.progress),
                255,
                60,
                60,
                200,
            )

    def _draw_pause_menu(self, draw_rectangle):
        left = SCREEN_WIDTH / 2 - 300
        right = SCREEN_WIDTH / 2 + 300
        bottom = SCREEN_HEIGHT / 2 - 170
        top = SCREEN_HEIGHT / 2 + 170
        draw_rectangle(left, bottom, right, top, 20, 25, 35, 225, True)
        draw_centered_text(
            self.hud_font,
            SCREEN_HEIGHT / 2 + 104,
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
                SCREEN_HEIGHT / 2 + 24 - index * 68,
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
            SCREEN_HEIGHT / 2 + 80,
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
            SCREEN_HEIGHT / 2 - 80,
            "PRESS SPACE TO RETURN TO LOBBY",
            (255, 255, 255),
        )

    def _draw_aim_cursor(self, draw_rectangle):
        cursor_x, cursor_y = self.aim_cursor_position
        radius = AIM_CURSOR_RADIUS
        gap = AIM_CURSOR_GAP
        half = AIM_CURSOR_THICKNESS / 2.0
        segments = (
            (cursor_x - radius, cursor_y - half, cursor_x - gap, cursor_y + half),
            (cursor_x + gap, cursor_y - half, cursor_x + radius, cursor_y + half),
            (cursor_x - half, cursor_y - radius, cursor_x + half, cursor_y - gap),
            (cursor_x - half, cursor_y + gap, cursor_x + half, cursor_y + radius),
        )
        for x1, y1, x2, y2 in segments:
            draw_rectangle(
                x1,
                y1,
                x2,
                y2,
                AIM_CURSOR_COLOR[0],
                AIM_CURSOR_COLOR[1],
                AIM_CURSOR_COLOR[2],
                AIM_CURSOR_ALPHA,
                True,
            )
        draw_rectangle(
            cursor_x - half,
            cursor_y - half,
            cursor_x + half,
            cursor_y + half,
            AIM_CURSOR_COLOR[0],
            AIM_CURSOR_COLOR[1],
            AIM_CURSOR_COLOR[2],
            AIM_CURSOR_ALPHA,
            True,
        )

    def _draw_pickups(self, draw_rectangle):
        groups = (
            (self.pickups, (235, 190, 65)),
            (self.health_pickups, (235, 70, 70)),
            (self.cooling_pickups, (80, 140, 255)),
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
            SCREEN_HEIGHT - 260,
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
        margin = max(getattr(obj, "radius", 0), 24)
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
            SCREEN_HEIGHT - menu_bottom - 16,
            SCREEN_WIDTH - 16,
            SCREEN_HEIGHT - 16,
            25,
            30,
            40,
            230,
            True,
        )
        self.debug_font.draw(
            DEBUG_MENU_LEFT + 16,
            SCREEN_HEIGHT - 60,
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
                left + 12,
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
