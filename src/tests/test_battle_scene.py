import math
import random
import unittest
from unittest import mock

from audio import (
    BATTLE_MUSIC_FILE,
    BATTLE_PORTAL_EXIT_SOUND_FILE,
    DEFEAT_MUSIC_FILE,
    OVERHEAT_SOUND_FILE,
    PISTOL_SHOT_SOUND_FILE,
    RELOAD_SOUND_FILE,
    VICTORY_MUSIC_FILE,
)
from battle_scene import BattleResult, BattleScene
import battle_scene
from enemy import Enemy, EnemyType
from game_config import (
    AIM_CURSOR_RADIUS,
    PICKUP_DRAW_SIZE,
    PLAYER_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
import game_world
import hud
from player import Player
from pickup import CoolingPickup, HealthPickup, MagazinePickup
from weapon import (
    DEFAULT_GUN_ID,
    Gun,
    MACHINE_GUN_GUN_ID,
    RIFLE_GUN_ID,
)
from waves import WaveDirector


class FakeBackground:
    def draw(self, *args):
        pass


class RecordingBackground:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, width=None, height=None):
        self.draws.append((x, y, width, height))


class FakeImage:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, w=None, h=None):
        self.draws.append((x, y, w, h))


class FakeGunImage(FakeImage):
    def __init__(self, texture="gun-texture"):
        super().__init__()
        self.texture = texture
        self.composite_draws = []

    def composite_draw(self, rad, flip, x, y, w=None, h=None):
        self.composite_draws.append((rad, flip, x, y, w, h))


class FakeFont:
    def draw(self, *args):
        pass


class RecordingAudio:
    def __init__(self):
        self.events = []

    def play(self, name):
        self.events.append(("play", name))

    def play_once(self, name):
        self.events.append(("play_once", name))

    def play_sound(self, name, target_duration=None):
        if target_duration is None:
            self.events.append(("play_sound", name))
        else:
            self.events.append(("play_sound", name, target_duration))

    def pause_sound(self, name):
        self.events.append(("pause_sound", name))

    def resume_sound(self, name):
        self.events.append(("resume_sound", name))

    def stop_sound(self, name):
        self.events.append(("stop_sound", name))

    def stop(self):
        self.events.append(("stop",))


class StubRandom:
    def __init__(self, coin=1, roll=1.0):
        self.coin = coin
        self.roll = roll

    def randint(self, minimum, maximum):
        return self.coin

    def random(self):
        return self.roll

    def uniform(self, minimum, maximum):
        return self.roll * (maximum - minimum) + minimum


class SequenceStubRandom(StubRandom):
    """Random stub that returns a fixed sequence of roll values."""

    def __init__(self, coin=1, rolls=None):
        super().__init__(coin=coin, roll=1.0)
        self.rolls = list(rolls or [])

    def random(self):
        if self.rolls:
            return self.rolls.pop(0)
        return self.roll


def make_scene(total_waves, spawn_rate, skip_countdown=True, audio=None):
    scene = BattleScene(
        Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
        Gun(),
        FakeBackground(),
        hud_font=FakeFont(),
        enemy_images={enemy_type: FakeImage() for enemy_type in EnemyType},
        enemy_draw_rectangle=lambda *args: None,
        enemy_draw_circle=lambda *args: None,
        random_source=random.Random(0),
        audio=audio,
    )
    scene.wave_director = WaveDirector(
        total_waves=total_waves,
        spawn_rate=spawn_rate,
        random_source=random.Random(0),
    )
    scene.spawn_warnings = []
    scene.waves_cleared = False
    if skip_countdown:
        scene.start_countdown_remaining = 0.0
        scene._announce_wave()
    return scene


def make_portal_transition_scene(portal_image=None, gun_image=None, audio=None):
    scene = BattleScene(
        Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
        Gun(),
        FakeBackground(),
        gun_image=gun_image,
        hud_font=FakeFont(),
        enemy_images={enemy_type: FakeImage() for enemy_type in EnemyType},
        enemy_draw_rectangle=lambda *args: None,
        enemy_draw_circle=lambda *args: None,
        random_source=random.Random(0),
        portal_image=portal_image,
        portal_transition=True,
        audio=audio,
    )
    return scene


def alive_enemies():
    return [
        obj
        for layer in game_world.world
        for obj in layer
        if isinstance(obj, Enemy) and obj.is_alive
    ]


class BattleSceneWaveTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_battle_starts_without_spawned_enemies(self):
        self.assertEqual(alive_enemies(), [])
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(self.scene.wave_director.current_wave, 1)

    def test_spawning_creates_warnings_before_enemies(self):
        self.scene.update(0.1)

        self.assertEqual(len(self.scene.spawn_warnings), 10)
        self.assertEqual(alive_enemies(), [])

    def test_enemies_appear_after_warning_expires(self):
        self.scene.update(0.1)

        self.scene.update(0.5)

        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(len(alive_enemies()), 10)

    def test_clearing_every_enemy_finishes_the_last_wave(self):
        self.scene.update(0.1)
        self.scene.update(0.5)
        for enemy in alive_enemies():
            enemy.hp = 0

        self.scene.update(0.0)

        self.assertEqual(alive_enemies(), [])
        self.assertTrue(self.scene.waves_cleared)
        self.assertEqual(self.scene.wave_banner_text, "ALL WAVES CLEARED")

    def test_clearing_a_wave_advances_to_the_next_wave(self):
        scene = make_scene(total_waves=2, spawn_rate=1000)
        scene.update(0.1)
        scene.update(0.5)
        for enemy in alive_enemies():
            enemy.hp = 0

        scene.update(0.0)

        self.assertFalse(scene.waves_cleared)
        self.assertEqual(scene.wave_director.current_wave, 2)
        self.assertEqual(scene.reached_wave, 2)
        self.assertEqual(scene.wave_banner_text, "WAVE 2")

    def test_wave_enemies_use_the_wave_stat_multiplier(self):
        self.scene.wave_director.current_wave = 10

        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 500,
            self.scene.player.y,
        )

        self.assertEqual(enemy.max_hp, 40)
        self.assertEqual(enemy.attack_damage, 16)

    def test_remaining_enemy_count_includes_queued_warnings_and_alive(self):
        total = self.scene.wave_director.total_to_spawn
        self.assertEqual(self.scene._remaining_enemy_count(), total)

        self.scene.update(0.1)
        self.assertEqual(self.scene._remaining_enemy_count(), total)

        self.scene.update(0.5)
        enemies = alive_enemies()
        self.assertEqual(len(enemies), total)

        for enemy in enemies[:3]:
            enemy.hp = 0

        self.assertEqual(self.scene._remaining_enemy_count(), total - 3)

    def test_reset_map_restores_the_first_wave(self):
        self.scene.update(0.1)
        self.scene.waves_cleared = True
        self.scene.coins = 12
        self.scene.pickups.append(
            MagazinePickup(self.scene.player.x, self.scene.player.y, 5)
        )

        self.scene.reset_map()

        self.assertEqual(self.scene.wave_director.current_wave, 1)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertFalse(self.scene.waves_cleared)
        self.assertTrue(self.scene.is_counting_down)
        self.assertEqual(self.scene.wave_banner_text, "")
        self.assertEqual(alive_enemies(), [])
        self.assertEqual(self.scene.coins, 0)
        self.assertEqual(self.scene.pickups, [])


class BattleSceneStartCountdownTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(
            total_waves=1,
            spawn_rate=1000,
            skip_countdown=False,
        )

    def tearDown(self):
        game_world.clear()

    def test_battle_starts_after_three_seconds(self):
        self.assertTrue(self.scene.is_counting_down)
        self.assertEqual(self.scene.start_countdown_remaining, 3.0)
        self.assertEqual(self.scene.wave_banner_text, "")

        self.scene.update(2.9)

        self.assertTrue(self.scene.is_counting_down)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(self.scene.elapsed_time, 0.0)

        self.scene.update(0.2)

        self.assertFalse(self.scene.is_counting_down)
        self.assertEqual(self.scene.wave_banner_text, "WAVE 1")

        self.scene.update(0.1)

        self.assertEqual(len(self.scene.spawn_warnings), 10)
        self.assertAlmostEqual(self.scene.elapsed_time, 0.1)

    def test_player_can_move_during_the_countdown(self):
        start_x = self.scene.player.x
        self.scene.keys.add("d")

        self.scene.update(1.0)

        self.assertGreater(self.scene.player.x, start_x)
        self.assertTrue(self.scene.is_counting_down)

    def test_gun_does_not_fire_during_the_countdown(self):
        magazine_ammo = self.scene.gun.magazine_ammo
        self.scene.mouse_down("left")

        self.scene.update(0.0)

        self.assertEqual(self.scene.gun_recoil_remaining, 0.0)
        self.assertEqual(self.scene.gun.magazine_ammo, magazine_ammo)

    def test_gun_fires_after_the_countdown(self):
        self.scene.update(3.0)
        self.scene.mouse_down("left")

        self.scene.update(0.0)

        self.assertEqual(
            self.scene.gun_recoil_remaining,
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS,
        )

    def test_escape_does_not_pause_during_the_countdown(self):
        self.scene.key_down("escape")
        self.assertFalse(self.scene.paused)

        self.scene.key_up("escape")
        self.scene.update(3.0)
        self.scene.key_down("escape")

        self.assertTrue(self.scene.paused)

    def test_countdown_number_is_drawn(self):
        self.scene.player.image = FakeImage()
        with mock.patch("battle_scene.draw_hud"), mock.patch(
            "battle_scene.draw_centered_text"
        ) as draw_text:
            self.scene.draw(lambda *args: None)

        draw_text.assert_any_call(
            self.scene.hud_font,
            SCREEN_HEIGHT * 3 / 4,
            "3",
            (255, 220, 100),
        )


class BattleSceneMusicTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def make_audio_scene(self, total_waves=1, skip_countdown=True):
        audio = RecordingAudio()
        scene = make_scene(
            total_waves=total_waves,
            spawn_rate=1000,
            skip_countdown=skip_countdown,
            audio=audio,
        )
        return scene, audio

    def test_music_starts_immediately_when_there_is_no_entry_animation(self):
        _scene, audio = self.make_audio_scene(skip_countdown=False)

        self.assertEqual(audio.events, [("play", BATTLE_MUSIC_FILE)])

    def test_music_starts_when_the_portal_entry_animation_ends(self):
        audio = RecordingAudio()
        scene = make_portal_transition_scene(audio=audio)
        audio.events.clear()

        scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS)
        scene.update(battle_scene.BATTLE_PORTAL_FADE_SECONDS)

        self.assertEqual(audio.events, [])

        scene.update(battle_scene.BATTLE_PORTAL_CAMERA_PAN_SECONDS)

        self.assertEqual(audio.events, [("play", BATTLE_MUSIC_FILE)])
        self.assertTrue(scene.is_counting_down)

        audio.events.clear()
        scene.update(3.0)

        self.assertEqual(audio.events, [])

    def test_music_continues_through_wave_advances(self):
        scene, audio = self.make_audio_scene(total_waves=2)
        audio.events.clear()

        scene.update(0.1)
        scene.update(0.5)
        for enemy in alive_enemies():
            enemy.hp = 0
        scene.update(0.0)

        self.assertEqual(audio.events, [])

    def test_pause_stops_music_and_resume_starts_it_again(self):
        scene, audio = self.make_audio_scene()
        audio.events.clear()

        scene.key_down("escape")
        self.assertEqual(
            audio.events,
            [("stop",), ("pause_sound", RELOAD_SOUND_FILE)],
        )

        scene.key_up("escape")
        scene.key_down("escape")

        self.assertEqual(
            audio.events[2:],
            [("play", BATTLE_MUSIC_FILE), ("resume_sound", RELOAD_SOUND_FILE)],
        )

    def test_defeat_plays_the_lose_track_once(self):
        scene, audio = self.make_audio_scene()
        scene.player.hp = 0
        audio.events.clear()

        scene.update(0.0)

        self.assertEqual(
            audio.events,
            [
                ("stop",),
                ("stop_sound", RELOAD_SOUND_FILE),
                ("play_once", DEFEAT_MUSIC_FILE),
            ],
        )

    def test_defeat_does_not_replay_the_lose_track_on_later_updates(self):
        scene, audio = self.make_audio_scene()
        scene.player.hp = 0
        audio.events.clear()

        scene.update(0.0)
        scene.update(0.5)

        self.assertEqual(
            audio.events,
            [
                ("stop",),
                ("stop_sound", RELOAD_SOUND_FILE),
                ("play_once", DEFEAT_MUSIC_FILE),
            ],
        )

    def test_victory_plays_the_win_track_once(self):
        scene, audio = self.make_audio_scene()
        scene.waves_cleared = True
        audio.events.clear()

        scene.update(0.0)

        self.assertEqual(
            audio.events,
            [
                ("stop",),
                ("stop_sound", RELOAD_SOUND_FILE),
                ("play_once", VICTORY_MUSIC_FILE),
            ],
        )

    def test_victory_does_not_replay_the_win_track_on_later_updates(self):
        scene, audio = self.make_audio_scene()
        scene.waves_cleared = True
        audio.events.clear()

        scene.update(0.0)
        scene.update(0.5)

        self.assertEqual(
            audio.events,
            [
                ("stop",),
                ("stop_sound", RELOAD_SOUND_FILE),
                ("play_once", VICTORY_MUSIC_FILE),
            ],
        )

    def test_quit_stops_music(self):
        scene, audio = self.make_audio_scene()
        scene.paused = True
        scene.pause_menu_index = 1
        audio.events.clear()

        scene.key_down("space")

        self.assertEqual(
            audio.events,
            [("stop",), ("stop_sound", RELOAD_SOUND_FILE)],
        )

    def test_reset_map_restarts_music_without_an_entry_animation(self):
        scene, audio = self.make_audio_scene()
        audio.events.clear()

        scene.reset_map()

        self.assertEqual(
            audio.events,
            [
                ("stop",),
                ("stop_sound", RELOAD_SOUND_FILE),
                ("play", BATTLE_MUSIC_FILE),
            ],
        )

        audio.events.clear()
        scene.update(3.0)

        self.assertEqual(audio.events, [])


class BattleSceneShotSoundTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def make_audio_scene(self, gun_id=DEFAULT_GUN_ID):
        audio = RecordingAudio()
        scene = make_scene(total_waves=1, spawn_rate=1000, audio=audio)
        scene.gun = Gun.from_gun_id(gun_id)
        audio.events.clear()
        return scene, audio

    def fire_once(self, scene):
        scene.mouse_down("left")
        scene.update(0.0)
        scene.mouse_up("left")
        scene.gun.cooldown_remaining = 0.0

    def test_every_pistol_shot_plays_the_sound_once(self):
        scene, audio = self.make_audio_scene()

        self.fire_once(scene)
        self.fire_once(scene)

        self.assertEqual(
            audio.events,
            [
                ("play_sound", PISTOL_SHOT_SOUND_FILE),
                ("play_sound", PISTOL_SHOT_SOUND_FILE),
            ],
        )

    def test_other_guns_do_not_play_the_pistol_sound(self):
        scene, audio = self.make_audio_scene(gun_id=RIFLE_GUN_ID)

        self.fire_once(scene)

        self.assertGreater(scene.gun_recoil_remaining, 0.0)
        self.assertEqual(audio.events, [])


class BattleSceneOverheatSoundTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def make_audio_scene(self):
        audio = RecordingAudio()
        scene = make_scene(total_waves=1, spawn_rate=1000, audio=audio)
        audio.events.clear()
        return scene, audio

    def overheat_with_one_shot(self, scene):
        scene.gun.temperature = scene.gun.temperature_limit - 0.2
        scene.gun.cooldown_remaining = 0.0
        scene.mouse_down("left")
        scene.update(0.0)
        scene.mouse_up("left")

    def test_overheat_plays_the_sound_once(self):
        scene, audio = self.make_audio_scene()

        self.overheat_with_one_shot(scene)

        self.assertTrue(scene.gun.overheated)
        self.assertEqual(
            audio.events,
            [
                ("play_sound", OVERHEAT_SOUND_FILE),
                ("play_sound", PISTOL_SHOT_SOUND_FILE),
            ],
        )

    def test_blocked_shots_do_not_replay_the_overheat_sound(self):
        scene, audio = self.make_audio_scene()
        self.overheat_with_one_shot(scene)
        audio.events.clear()

        scene.mouse_down("left")
        scene.update(0.0)
        scene.mouse_up("left")

        self.assertEqual(audio.events, [])


class BattleSceneReloadSoundTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def make_audio_scene(self, gun_id=DEFAULT_GUN_ID):
        audio = RecordingAudio()
        scene = make_scene(total_waves=1, spawn_rate=1000, audio=audio)
        scene.gun = Gun.from_gun_id(gun_id)
        audio.events.clear()
        return scene, audio

    def test_pressing_r_plays_the_reload_sound_once(self):
        scene, audio = self.make_audio_scene()
        scene.gun.magazine_ammo = 0

        scene.key_down("r")

        self.assertTrue(scene.gun.reloading)
        self.assertEqual(
            audio.events,
            [("play_sound", RELOAD_SOUND_FILE, scene.gun.reload_seconds)],
        )

    def test_repeated_r_while_reloading_does_not_replay_the_sound(self):
        scene, audio = self.make_audio_scene()
        scene.gun.magazine_ammo = 0

        scene.key_down("r")
        scene.key_up("r")
        scene.key_down("r")

        self.assertEqual(
            audio.events,
            [("play_sound", RELOAD_SOUND_FILE, scene.gun.reload_seconds)],
        )

    def test_reload_without_needed_ammo_plays_no_sound(self):
        scene, audio = self.make_audio_scene()

        scene.key_down("r")

        self.assertFalse(scene.gun.reloading)
        self.assertEqual(audio.events, [])

    def test_automatic_reload_plays_the_sound_once(self):
        scene, audio = self.make_audio_scene(gun_id=RIFLE_GUN_ID)
        scene.gun.magazine_ammo = 0

        scene.mouse_down("left")
        scene.update(0.0)
        scene.mouse_up("left")

        self.assertTrue(scene.gun.reloading)
        self.assertEqual(
            audio.events,
            [("play_sound", RELOAD_SOUND_FILE, scene.gun.reload_seconds)],
        )

    def test_firing_with_ammo_plays_no_reload_sound(self):
        scene, audio = self.make_audio_scene()

        scene.mouse_down("left")
        scene.update(0.0)
        scene.mouse_up("left")

        self.assertEqual(
            audio.events,
            [("play_sound", PISTOL_SHOT_SOUND_FILE)],
        )

    def test_each_gun_uses_its_own_reload_duration(self):
        for gun_id in (DEFAULT_GUN_ID, RIFLE_GUN_ID, MACHINE_GUN_GUN_ID):
            with self.subTest(gun_id=gun_id):
                game_world.clear()
                scene, audio = self.make_audio_scene(gun_id=gun_id)
                scene.gun.magazine_ammo = 0

                scene.key_down("r")

                self.assertEqual(
                    audio.events,
                    [("play_sound", RELOAD_SOUND_FILE, scene.gun.reload_seconds)],
                )

    def test_reload_without_audio_is_safe(self):
        scene = make_scene(total_waves=1, spawn_rate=1000)
        scene.gun.magazine_ammo = 0

        scene.key_down("r")

        self.assertTrue(scene.gun.reloading)

    def test_pausing_pauses_the_reload_sound(self):
        scene, audio = self.make_audio_scene()
        scene.gun.magazine_ammo = 0
        scene.key_down("r")
        audio.events.clear()

        scene.key_down("escape")

        self.assertEqual(
            audio.events,
            [("stop",), ("pause_sound", RELOAD_SOUND_FILE)],
        )

    def test_resuming_resumes_the_reload_sound(self):
        scene, audio = self.make_audio_scene()
        scene.gun.magazine_ammo = 0
        scene.key_down("r")
        scene.key_down("escape")
        scene.key_up("escape")
        audio.events.clear()

        scene.key_down("escape")

        self.assertEqual(
            audio.events,
            [("play", BATTLE_MUSIC_FILE), ("resume_sound", RELOAD_SOUND_FILE)],
        )

    def test_resuming_from_the_pause_menu_resumes_the_reload_sound(self):
        scene, audio = self.make_audio_scene()
        scene.key_down("escape")
        scene.key_up("escape")
        audio.events.clear()

        scene.key_down("space")

        self.assertEqual(
            audio.events,
            [("play", BATTLE_MUSIC_FILE), ("resume_sound", RELOAD_SOUND_FILE)],
        )


class BattleScenePortalTransitionTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_portal_transition_scene()

    def tearDown(self):
        game_world.clear()

    def test_transition_starts_at_the_center_with_the_system_cursor(self):
        start_x, start_y = self.scene.portal_transition_start_position
        end_x, end_y = self.scene.portal_transition_end_position

        self.assertEqual(
            self.scene.portal_transition_start_position,
            self.scene.initial_player_position,
        )
        self.assertTrue(self.scene.portal_transition_active)
        self.assertEqual((self.scene.player.x, self.scene.player.y), (start_x, start_y))
        self.assertGreater(start_y, end_y)
        self.assertFalse(self.scene.portal_fade_active)
        self.assertFalse(self.scene.is_counting_down)
        self.assertFalse(self.scene.shows_aim_cursor)
        self.assertTrue(self.scene.shows_system_cursor)
        self.assertEqual(self.scene.start_countdown_remaining, 3.0)

    def test_transition_plays_the_portal_exit_sound_once(self):
        audio = RecordingAudio()

        make_portal_transition_scene(audio=audio)

        self.assertEqual(
            audio.events,
            [("play_sound", BATTLE_PORTAL_EXIT_SOUND_FILE)],
        )

    def test_transition_without_audio_is_safe(self):
        scene = make_portal_transition_scene(audio=None)

        self.assertTrue(scene.portal_transition_active)

    def test_transition_moves_down_and_decelerates_geometrically(self):
        start_y = self.scene.portal_transition_start_position[1]
        end_y = self.scene.portal_transition_end_position[1]
        total_distance = start_y - end_y

        self.scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS / 2)
        first_half_distance = start_y - self.scene.player.y
        mid_transition_angle = self.scene.portal_transition_angle

        self.scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS / 2)
        second_half_distance = (start_y - first_half_distance) - self.scene.player.y

        self.assertGreater(first_half_distance, second_half_distance * 3.0)
        self.assertGreater(first_half_distance, total_distance * 0.7)
        self.assertGreater(mid_transition_angle, 0.0)
        self.assertTrue(self.scene.portal_fade_active)
        self.assertTrue(self.scene.portal_transition_active)
        self.assertFalse(self.scene.is_counting_down)

    def test_portal_fades_out_before_the_countdown_starts(self):
        self.scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS)

        self.assertEqual(
            (self.scene.player.x, self.scene.player.y),
            self.scene.portal_transition_end_position,
        )
        self.assertIsNone(self.scene.player.render_angle)
        self.assertIsNone(self.scene.player.render_opacity)
        self.assertIsNone(self.scene.player.render_scale)
        self.assertTrue(self.scene.portal_transition_active)
        self.assertFalse(self.scene.is_counting_down)
        camera_during_fade = (self.scene.camera.x, self.scene.camera.y)

        self.scene.update(battle_scene.BATTLE_PORTAL_FADE_SECONDS / 2)

        self.assertTrue(self.scene.portal_transition_active)
        self.assertFalse(self.scene.is_counting_down)
        self.assertFalse(self.scene.shows_aim_cursor)
        self.assertTrue(self.scene.shows_system_cursor)
        self.assertEqual((self.scene.camera.x, self.scene.camera.y), camera_during_fade)

        self.scene.update(battle_scene.BATTLE_PORTAL_FADE_SECONDS / 2)

        end_x, end_y = self.scene.portal_transition_end_position
        expected_camera_y = min(
            max(end_y - SCREEN_HEIGHT / 2, 0.0),
            WORLD_HEIGHT - SCREEN_HEIGHT,
        )
        self.assertTrue(self.scene.portal_camera_pan_active)
        self.assertEqual((self.scene.camera.x, self.scene.camera.y), camera_during_fade)
        self.assertTrue(self.scene.portal_transition_active)
        self.assertFalse(self.scene.portal_fade_active)
        self.assertFalse(self.scene.is_counting_down)

        self.scene.update(battle_scene.BATTLE_PORTAL_CAMERA_PAN_SECONDS / 2)

        self.assertLess(self.scene.camera.y, camera_during_fade[1])
        self.assertGreater(self.scene.camera.y, expected_camera_y)
        self.assertTrue(self.scene.portal_camera_pan_active)
        self.assertFalse(self.scene.is_counting_down)

        self.scene.update(battle_scene.BATTLE_PORTAL_CAMERA_PAN_SECONDS / 2)

        self.assertAlmostEqual(self.scene.camera.y, expected_camera_y)
        self.assertFalse(self.scene.portal_camera_pan_active)
        self.assertFalse(self.scene.portal_transition_active)
        self.assertFalse(self.scene.portal_fade_active)
        self.assertTrue(self.scene.is_counting_down)
        self.assertEqual(self.scene.start_countdown_remaining, 3.0)
        self.assertTrue(self.scene.shows_aim_cursor)
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.update(3.0)

        self.assertFalse(self.scene.is_counting_down)
        self.assertEqual(self.scene.wave_banner_text, "WAVE 1")

    def test_fading_portal_image_becomes_transparent_then_is_restored(self):
        portal_image = mock.MagicMock()
        scene = make_portal_transition_scene(portal_image)
        scene.player.image = mock.MagicMock()
        scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS)
        scene.update(battle_scene.BATTLE_PORTAL_FADE_SECONDS / 2)
        portal_image.opacify.reset_mock()

        scene.draw(lambda *args: None)

        self.assertEqual(
            portal_image.opacify.call_args_list,
            [mock.call(0.5), mock.call(1.0)],
        )

    def test_portal_image_is_not_drawn_during_the_camera_pan(self):
        portal_image = mock.MagicMock()
        scene = make_portal_transition_scene(portal_image)
        scene.player.image = mock.MagicMock()
        scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS)
        scene.update(battle_scene.BATTLE_PORTAL_FADE_SECONDS)

        scene.draw(lambda *args: None)

        portal_image.draw.assert_not_called()

    def test_transition_draws_the_equipped_gun_with_the_player_transform(self):
        gun_image = mock.MagicMock()
        gun_image.texture = None
        scene = make_portal_transition_scene(gun_image=gun_image)
        scene.player.image = mock.MagicMock()
        scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS / 2)

        scene.draw(lambda *args: None)

        angle, flip, x, y, width, height = gun_image.composite_draw.call_args.args
        player_x, player_y = scene.player.screen_position
        reverse_angle = -(
            battle_scene.BATTLE_PORTAL_EXIT_ROTATIONS * math.tau
            - scene.portal_transition_angle
        )
        final_x = (
            math.cos(scene.player.aim_angle) * PLAYER_RADIUS * 0.6
            - scene._gun_pivot_left_offset()
        )
        final_y = (
            math.sin(scene.player.aim_angle) * PLAYER_RADIUS * 0.6
            - scene._gun_pivot_y_offset()
        )
        cosine = math.cos(reverse_angle)
        sine = math.sin(reverse_angle)
        expected_offset_x = (
            final_x * cosine - final_y * sine
        ) * scene.portal_transition_scale
        expected_offset_y = (
            final_x * sine + final_y * cosine
        ) * scene.portal_transition_scale

        self.assertAlmostEqual(angle, reverse_angle)
        self.assertEqual(flip, "")
        self.assertAlmostEqual(x, player_x + expected_offset_x)
        self.assertAlmostEqual(y, player_y + expected_offset_y)
        self.assertLess(
            math.hypot(x - player_x, y - player_y),
            PLAYER_RADIUS * 0.6 + 1.0,
        )
        self.assertAlmostEqual(width, 126 * scene.portal_transition_scale)
        self.assertAlmostEqual(height, 72 * scene.portal_transition_scale)
        self.assertEqual(
            gun_image.opacify.call_args_list,
            [mock.call(scene.portal_transition_opacity), mock.call(1.0)],
        )

    def test_gun_returns_to_the_battle_position_after_player_animation(self):
        gun_image = mock.MagicMock()
        gun_image.texture = None
        scene = make_portal_transition_scene(gun_image=gun_image)
        scene.player.image = mock.MagicMock()
        scene.update(battle_scene.BATTLE_PORTAL_EXIT_SECONDS)
        gun_image.composite_draw.reset_mock()

        scene.draw(lambda *args: None)

        angle, flip, x, y, width, height = gun_image.composite_draw.call_args.args
        player_x, player_y = scene.player.screen_position
        expected_x = (
            player_x
            + math.cos(scene.player.aim_angle) * PLAYER_RADIUS * 0.6
            - scene._gun_pivot_left_offset()
        )
        expected_y = (
            player_y
            + math.sin(scene.player.aim_angle) * PLAYER_RADIUS * 0.6
            - scene._gun_pivot_y_offset()
        )
        self.assertAlmostEqual(x, expected_x)
        self.assertAlmostEqual(y, expected_y)
        self.assertAlmostEqual(width, 126)
        self.assertAlmostEqual(height, 72)
        gun_image.opacify.assert_not_called()

    def test_transition_ignores_gameplay_input(self):
        self.scene.key_down("d")
        self.scene.mouse_down("left")

        self.assertEqual(self.scene.keys, set())
        self.assertFalse(self.scene.mouse_held)
        self.assertFalse(self.scene.paused)

    def test_transition_draws_the_portal_image_and_no_hud(self):
        portal_image = mock.MagicMock()
        scene = make_portal_transition_scene(portal_image)
        scene.player.image = mock.MagicMock()

        with mock.patch("battle_scene.draw_hud") as draw_hud, mock.patch(
            "battle_scene.draw_centered_text"
        ) as draw_text:
            scene.draw(lambda *args: None)

        portal_image.draw.assert_called_once_with(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            battle_scene.BATTLE_PORTAL_IMAGE_WIDTH,
            battle_scene.BATTLE_PORTAL_IMAGE_HEIGHT,
        )
        draw_hud.assert_not_called()
        draw_text.assert_not_called()


class BattleSceneRewardTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_defeating_an_enemy_awards_coins_and_can_drop_a_magazine(self):
        self.scene.random_source = SequenceStubRandom(coin=4, rolls=[0.9, 0.9, 0.0])

        self._defeat_one_enemy()

        self.assertEqual(self.scene.coins, 4)
        self.assertEqual(len(self.scene.pickups), 1)
        self.assertEqual(self.scene.pickups[0].amount, 10)

    def test_magazine_can_drop_at_three_hundred_or_more_ammo(self):
        self.scene.random_source = SequenceStubRandom(coin=2, rolls=[0.9, 0.9, 0.0])
        self.scene.gun.magazine_ammo = 10
        self.scene.gun.reserve_ammo = 290

        self._defeat_one_enemy()

        self.assertEqual(self.scene.coins, 2)
        self.assertEqual(len(self.scene.pickups), 1)

    def test_no_magazine_drops_when_the_roll_reaches_thirty_percent(self):
        self.scene.random_source = StubRandom(coin=2, roll=0.30)
        self.scene.gun.magazine_ammo = 10
        self.scene.gun.reserve_ammo = 290

        self._defeat_one_enemy()

        self.assertEqual(self.scene.coins, 2)
        self.assertEqual(self.scene.pickups, [])

    def test_health_drop_replaces_the_magazine_drop(self):
        self.scene.player.hp = 50
        self.scene.random_source = SequenceStubRandom(coin=1, rolls=[0.0])

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertEqual(self.scene.pickups, [])

    def test_magazine_drop_replaces_the_health_drop(self):
        self.scene.player.hp = 50
        self.scene.random_source = SequenceStubRandom(
            coin=1,
            rolls=[0.9, 0.9, 0.0],
        )

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.pickups), 1)
        self.assertEqual(self.scene.health_pickups, [])

    def test_only_one_drop_type_appears_per_enemy(self):
        self.scene.player.hp = 50

        for rolls in ([0.0, 0.9, 0.9], [0.9, 0.0, 0.9], [0.9, 0.9, 0.0], [0.0, 0.0, 0.9]):
            self.scene.pickups = []
            self.scene.health_pickups = []
            self.scene.cooling_pickups = []
            self.scene.random_source = SequenceStubRandom(coin=1, rolls=list(rolls))

            self._defeat_one_enemy()

            total = (
                len(self.scene.pickups)
                + len(self.scene.health_pickups)
                + len(self.scene.cooling_pickups)
            )
            self.assertLessEqual(total, 1, "한 번의 처치로 두 종류가 함께 드롭되면 안 된다")

    def test_health_drop_is_skipped_when_the_map_limit_is_reached(self):
        self.scene.player.hp = 50
        self.scene.health_pickups = [
            HealthPickup(0.0, 0.0),
            HealthPickup(10.0, 10.0),
        ]
        self.scene.cooling_pickups = []
        self.scene.random_source = SequenceStubRandom(coin=1, rolls=[0.9, 0.0])

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 2)
        self.assertEqual(len(self.scene.pickups), 1)

    def test_explosive_self_destruct_does_not_drop_items(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.EXPLOSIVE,
            self.scene.player.x,
            self.scene.player.y,
        )

        self.scene.update(0.0)

        self.assertFalse(enemy.is_alive)
        self.assertEqual(self.scene.health_pickups, [])
        self.assertEqual(self.scene.pickups, [])

    def test_explosive_killed_by_player_still_drops_items(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.EXPLOSIVE,
            self.scene.player.x + 300,
            self.scene.player.y,
        )

        enemy.take_damage(enemy.hp)
        self.scene.update(0.0)

        self.assertEqual(len(self.scene.health_pickups), 1)

    def test_enemy_killed_by_an_explosion_does_not_drop_items(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        victim = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        victim.hp = 10
        bomber = self.scene._spawn_wave_enemy(
            EnemyType.EXPLOSIVE,
            victim.x + 10,
            victim.y,
        )

        bomber.take_damage(bomber.hp)
        self.scene.update(0.0)

        self.assertFalse(victim.is_alive)
        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertEqual(self.scene.pickups, [])

    def test_walking_over_a_magazine_adds_reserve_ammo(self):
        self.scene.gun.magazine_ammo = 2
        self.scene.gun.reserve_ammo = 40
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
            )
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(self.scene.gun.magazine_ammo, 2)
        self.assertEqual(self.scene.gun.reserve_ammo, 50)
        self.assertEqual(self.scene.pickups, [])

    def test_full_magazine_still_takes_the_pickup(self):
        self.scene.gun.magazine_ammo = self.scene.gun.spec.magazine_size
        self.scene.gun.reserve_ammo = 40
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
            )
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(
            self.scene.gun.magazine_ammo,
            self.scene.gun.spec.magazine_size,
        )
        self.assertEqual(self.scene.gun.reserve_ammo, 50)
        self.assertEqual(len(self.scene.pickups), 0)


class BattleScenePickupImageTests(unittest.TestCase):
    def setUp(self):
        self.ammo_image = FakeImage()
        self.health_image = FakeImage()
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.scene.ammo_image = self.ammo_image
        self.scene.health_image = self.health_image

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_magazine_drop_uses_the_ammo_image(self):
        self.scene.random_source = SequenceStubRandom(coin=1, rolls=[0.9, 0.9, 0.0])

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.pickups), 1)
        self.assertIs(self.scene.pickups[0].image, self.ammo_image)

    def test_health_drop_uses_the_health_image(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertIs(self.scene.health_pickups[0].image, self.health_image)

    def test_pickups_are_drawn_with_their_images(self):
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
                image=self.ammo_image,
            )
        )
        self.scene.health_pickups.append(
            HealthPickup(
                self.scene.player.x,
                self.scene.player.y,
                image=self.health_image,
            )
        )
        rectangles = []

        self.scene._draw_pickups(
            lambda x1, y1, x2, y2, *args: rectangles.append((x1, y1, x2, y2))
        )

        self.assertEqual(len(self.ammo_image.draws), 1)
        self.assertEqual(len(self.health_image.draws), 1)
        self.assertEqual(rectangles, [])

    def test_pickup_images_are_drawn_at_the_pickup_position(self):
        pickup = MagazinePickup(
            self.scene.player.x,
            self.scene.player.y,
            10,
            image=self.ammo_image,
        )
        self.scene.pickups.append(pickup)

        self.scene._draw_pickups(lambda *args: None)

        screen_x, screen_y, width, height = self.ammo_image.draws[0]
        expected_x, expected_y = self.scene.camera.world_to_screen(
            self.scene.player.x,
            self.scene.player.y,
        )
        self.assertAlmostEqual(screen_x, expected_x)
        self.assertAlmostEqual(screen_y, expected_y)
        self.assertEqual(width, PICKUP_DRAW_SIZE)
        self.assertEqual(height, PICKUP_DRAW_SIZE)

    def test_pickup_without_image_falls_back_to_a_rectangle(self):
        self.scene.pickups.append(
            MagazinePickup(self.scene.player.x, self.scene.player.y, 10)
        )
        rectangles = []

        self.scene._draw_pickups(
            lambda x1, y1, x2, y2, *args: rectangles.append((x1, y1, x2, y2))
        )

        self.assertEqual(len(rectangles), 1)


class BattleSceneHealthDropTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_damaged_player_can_receive_a_health_drop(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertEqual(self.scene.health_pickups[0].amount, 10)

    def test_full_hp_player_never_receives_a_health_drop(self):
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(self.scene.health_pickups, [])

    def test_no_health_drop_when_two_are_already_on_the_map(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        self.scene.health_pickups = [
            HealthPickup(0.0, 0.0),
            HealthPickup(10.0, 10.0),
        ]

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 2)

    def test_collected_health_items_no_longer_count_toward_the_limit(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        self.scene.health_pickups = [
            HealthPickup(0.0, 0.0),
            HealthPickup(10.0, 10.0),
        ]
        self.scene.health_pickups.pop()

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 2)

    def test_walking_over_health_restores_ten_hp(self):
        self.scene.player.hp = 50
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(self.scene.player.hp, 60)
        self.assertEqual(self.scene.health_pickups, [])

    def test_health_pickup_respects_the_max_hp(self):
        self.scene.player.hp = 95
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(self.scene.player.hp, self.scene.player.max_hp)
        self.assertEqual(self.scene.health_pickups, [])

    def test_full_hp_player_leaves_the_health_pickup_on_the_map(self):
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(len(self.scene.health_pickups), 1)

    def test_overheated_gun_leaves_the_cooling_pickup_on_the_map(self):
        self.scene.gun.temperature = 100.0
        self.scene.gun.overheated = True
        self.scene.cooling_pickups.append(
            CoolingPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups(0.0)

        self.assertEqual(self.scene.gun.temperature, 100.0)
        self.assertEqual(len(self.scene.cooling_pickups), 1)

    def test_walking_over_cooling_item_reduces_temperature(self):
        self.scene.gun.temperature = 100.0
        self.scene.cooling_pickups.append(
            CoolingPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups(0.0)

        self.assertLess(self.scene.gun.temperature, 100.0)
        self.assertEqual(self.scene.cooling_pickups, [])


class BattleSceneFlowTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_escape_pauses_the_battle_and_freezes_updates(self):
        self.scene.key_down("escape")

        self.scene.update(0.1)

        self.assertTrue(self.scene.paused)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(self.scene.gun.temperature, self.scene.gun.temperature)

    def test_escape_resumes_the_battle(self):
        self.scene.key_down("escape")
        self.scene.key_up("escape")

        self.scene.key_down("escape")

        self.assertFalse(self.scene.paused)

    def test_q_no_longer_pauses_the_battle(self):
        self.scene.key_down("q")

        self.assertFalse(self.scene.paused)

    def test_gameplay_keys_are_ignored_while_paused(self):
        original_mode = self.scene.gun.fire_mode
        self.scene.key_down("escape")

        self.scene.key_down("e")

        self.assertEqual(self.scene.gun.fire_mode, original_mode)

    def test_pause_menu_navigation_wraps_around(self):
        self.scene.key_down("escape")

        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 1)
        self.scene.key_up("s")
        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 0)
        self.scene.key_up("s")
        self.scene.key_down("w")
        self.assertEqual(self.scene.pause_menu_index, 1)

    def test_resume_option_closes_the_pause_menu(self):
        self.scene.key_down("escape")

        self.scene.key_down("space")

        self.assertFalse(self.scene.paused)
        self.assertFalse(self.scene.finished)

    def test_quit_option_finishes_the_battle(self):
        self.scene.key_down("escape")
        self.scene.key_down("s")
        self.scene.key_up("s")

        self.scene.key_down("space")

        self.assertTrue(self.scene.finished)
        self.assertFalse(self.scene.paused)
        self.assertIs(self.scene.result, BattleResult.QUIT)
        self.assertFalse(self.scene.exit_requested)

    def test_player_death_finishes_the_battle_as_a_defeat(self):
        self.scene.player.hp = 0

        self.scene.update(0.0)

        self.assertTrue(self.scene.finished)
        self.assertIs(self.scene.result, BattleResult.DEFEAT)

    def test_clearing_all_waves_finishes_the_battle_as_a_victory(self):
        self.scene.waves_cleared = True

        self.scene.update(0.0)

        self.assertTrue(self.scene.finished)
        self.assertIs(self.scene.result, BattleResult.VICTORY)

    def test_finished_battle_ignores_further_updates(self):
        self.scene.waves_cleared = True
        self.scene.update(0.0)
        warnings = list(self.scene.spawn_warnings)

        self.scene.update(1.0)

        self.assertEqual(self.scene.spawn_warnings, warnings)

    def test_enter_after_the_result_requests_leaving(self):
        self.scene.waves_cleared = True
        self.scene.update(0.0)

        self.scene.key_down("space")

        self.assertTrue(self.scene.exit_requested)

    def test_reset_map_clears_pause_and_result_state(self):
        self.scene.paused = True
        self.scene.finished = True
        self.scene.result = BattleResult.QUIT
        self.scene.exit_requested = True

        self.scene.reset_map()

        self.assertFalse(self.scene.paused)
        self.assertFalse(self.scene.finished)
        self.assertIsNone(self.scene.result)
        self.assertFalse(self.scene.exit_requested)


class BattleSceneHpTrailTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_player_hp_trail_lingers_after_damage(self):
        self.scene.player.take_damage(20)

        self.scene.update(0.1)

        self.assertEqual(self.scene.player.hp, 80)
        self.assertEqual(self.scene.player.hp_trail.value, 100)

    def test_enemy_hp_trail_lingers_after_damage(self):
        enemy = self.scene.spawn_enemy(
            EnemyType.BASIC,
            WORLD_WIDTH / 2,
            WORLD_HEIGHT / 2,
        )
        enemy.take_damage(5)

        self.scene.update(0.1)

        self.assertEqual(enemy.hp, 15)
        self.assertEqual(enemy.hp_trail.value, enemy.max_hp)


class BattleSceneDebugTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_debug_mode_enables_infinite_ammo_and_disables_heat(self):
        gun = self.scene.gun
        temperature = gun.temperature

        self.scene.key_down("f1")

        self.assertTrue(self.scene.debug_mode)
        self.assertTrue(gun.infinite_ammo)
        self.assertFalse(gun.heat_enabled)
        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.temperature, temperature)

    def test_leaving_debug_mode_restores_heat(self):
        self.scene.key_down("f1")
        self.scene.key_up("f1")

        self.scene.key_down("f1")

        self.assertFalse(self.scene.debug_mode)
        self.assertFalse(self.scene.gun.infinite_ammo)
        self.assertTrue(self.scene.gun.heat_enabled)

    def test_reset_map_keeps_heat_disabled_in_debug_mode(self):
        self.scene.key_down("f1")

        self.scene.reset_map()

        self.assertTrue(self.scene.debug_mode)
        self.assertTrue(self.scene.gun.infinite_ammo)
        self.assertFalse(self.scene.gun.heat_enabled)

    def test_debug_menu_has_add_coins_item(self):
        self.assertIn(("add_coins", "+10000 Coins"), battle_scene.DEBUG_MENU_ITEMS)

    def test_debug_menu_click_adds_ten_thousand_coins(self):
        self.scene.key_down("f1")
        self.scene.coins = 3
        index = [
            action for action, _ in battle_scene.DEBUG_MENU_ITEMS
        ].index("add_coins")
        left, top, right, bottom = self.scene._debug_button_bounds(index)

        self.scene.mouse_down("left", (left + right) / 2, (top + bottom) / 2)

        self.assertEqual(self.scene.coins, 10003)

    def test_debug_menu_draws_add_coins_label(self):
        self.scene.debug_mode = True

        with mock.patch.object(self.scene.debug_font, "draw") as draw:
            self.scene._draw_debug_menu(lambda *args: None)

        labels = [call.args[2] for call in draw.call_args_list]
        self.assertIn("+10000 Coins", labels)


class BattleSceneAimCursorTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.rectangles = []

    def tearDown(self):
        game_world.clear()

    def _draw_cursor(self):
        self.scene._draw_aim_cursor(
            lambda x1, y1, x2, y2, *args: self.rectangles.append((x1, y1, x2, y2))
        )
        return self.rectangles

    def test_cursor_position_follows_the_mouse(self):
        self.scene.mouse_move(300.0, 200.0)

        cursor_x, cursor_y = self.scene.aim_cursor_position

        self.assertEqual(cursor_x, 300.0)
        self.assertEqual(cursor_y, SCREEN_HEIGHT - 200.0)

    def test_aim_cursor_is_hidden_while_paused_or_finished(self):
        self.assertTrue(self.scene.shows_aim_cursor)

        self.scene.paused = True
        self.assertFalse(self.scene.shows_aim_cursor)

        self.scene.paused = False
        self.scene.finished = True
        self.assertFalse(self.scene.shows_aim_cursor)

    def test_system_cursor_shows_while_paused_or_finished(self):
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.paused = True
        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.paused = False
        self.scene.finished = True
        self.assertTrue(self.scene.shows_system_cursor)

    def test_system_cursor_shows_over_the_debug_menu(self):
        self.scene.debug_mode = True
        self.scene.mouse_move(battle_scene.DEBUG_MENU_LEFT + 50, 30)

        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.mouse_move(100, 100)

        self.assertFalse(self.scene.shows_system_cursor)

    def test_cursor_is_drawn_as_four_segments_and_a_center_dot(self):
        self.scene.mouse_move(300.0, 200.0)

        rectangles = self._draw_cursor()

        self.assertEqual(len(rectangles), 5)

    def test_cursor_segments_are_centered_on_the_cursor(self):
        self.scene.mouse_move(300.0, 200.0)

        rectangles = self._draw_cursor()

        for x1, y1, x2, y2 in rectangles:
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            if abs(center_x - 300.0) < 1e-9 and abs(center_y - 300.0) < 1e-9:
                continue
            self.assertTrue(
                abs(center_x - 300.0) <= AIM_CURSOR_RADIUS + 1e-9
                or abs(center_y - 300.0) <= AIM_CURSOR_RADIUS + 1e-9,
                "조준점 선분은 커서를 중심으로 대칭이어야 한다",
            )

    def test_cursor_moves_with_the_mouse(self):
        self.scene.mouse_move(300.0, 200.0)
        first = self._draw_cursor()
        first_center = (
            (first[0][0] + first[0][2]) / 2.0,
            (first[0][1] + first[0][3]) / 2.0,
        )

        self.rectangles = []
        self.scene.mouse_move(500.0, 300.0)
        second = self._draw_cursor()
        second_center = (
            (second[0][0] + second[0][2]) / 2.0,
            (second[0][1] + second[0][3]) / 2.0,
        )

        self.assertNotEqual(first_center, second_center)
        self.assertAlmostEqual(second_center[0] - first_center[0], 200.0)
        self.assertAlmostEqual(second_center[1] - first_center[1], -100.0)

    def test_cursor_is_drawn_with_the_scene(self):
        self.scene.mouse_move(300.0, 200.0)
        self.scene.player.image = FakeImage()

        with mock.patch.object(hud, "_measure_text_width", return_value=60):
            self.scene.draw(
                lambda x1, y1, x2, y2, *args: self.rectangles.append((x1, y1, x2, y2))
            )

        self.assertTrue(self.rectangles)


class BattleSceneBackgroundTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.scene.background = RecordingBackground()
        self.scene.player.image = FakeImage()

    def tearDown(self):
        game_world.clear()

    def _draw_scene(self):
        with mock.patch.object(hud, "_measure_text_width", return_value=60):
            self.scene.draw(lambda *args: None)

    def test_background_is_drawn_once_for_the_whole_map(self):
        self._draw_scene()

        self.assertEqual(len(self.scene.background.draws), 1)

    def test_background_covers_the_entire_world(self):
        self._draw_scene()

        _, _, width, height = self.scene.background.draws[0]
        self.assertEqual(width, WORLD_WIDTH)
        self.assertEqual(height, WORLD_HEIGHT)

    def test_background_scrolls_with_the_camera(self):
        self.scene.camera.x = 300.0
        self.scene.camera.y = 200.0

        self._draw_scene()

        x, y, _, _ = self.scene.background.draws[0]
        self.assertEqual(x, WORLD_WIDTH / 2 - 300.0)
        self.assertEqual(y, WORLD_HEIGHT / 2 - 200.0)


class BattleSceneGunTintTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.scene.player.image = FakeImage()
        self.gun_image = FakeGunImage()
        self.scene.gun_image = self.gun_image

    def tearDown(self):
        game_world.clear()

    def _draw_scene(self):
        with mock.patch.object(hud, "_measure_text_width", return_value=60):
            self.scene.draw(lambda *args: None)

    def _draw_with_calls(self):
        calls = []
        with mock.patch.object(
            battle_scene.pico2d,
            "SDL_SetTextureColorMod",
            side_effect=lambda *args: calls.append(args),
        ):
            self._draw_scene()
        return calls

    def _drawn_gun_position(self, gun_id):
        image = FakeGunImage(texture=None)
        self.scene.gun_image = image
        self.scene.player.set_screen_position(500, 500)
        self.scene.player.aim_angle = 0.0
        self.scene.gun = Gun.from_gun_id(gun_id)
        self.scene._draw_gun()
        return image.composite_draws[-1][2:4]

    def test_draw_uses_the_image_for_the_current_gun_id(self):
        pistol_image = FakeGunImage(texture=None)
        rifle_image = FakeGunImage(texture=None)
        self.scene.gun_image = pistol_image
        self.scene.gun_images = {"rifle": rifle_image}
        self.scene.gun = Gun.from_gun_id("rifle", 0)

        self.scene._draw_gun()

        self.assertEqual(len(rifle_image.composite_draws), 1)
        self.assertEqual(pistol_image.composite_draws, [])

    def test_pistol_pivot_is_unchanged(self):
        self.assertEqual(
            battle_scene.GUN_PIVOT_Y_OFFSETS[DEFAULT_GUN_ID],
            0.0,
        )
        self.assertEqual(
            battle_scene.GUN_PIVOT_LEFT_OFFSETS[DEFAULT_GUN_ID],
            0.0,
        )

    def test_rifle_is_ten_pixels_lower_than_the_pistol(self):
        pistol_x, pistol_y = self._drawn_gun_position(DEFAULT_GUN_ID)
        rifle_x, rifle_y = self._drawn_gun_position(RIFLE_GUN_ID)

        self.assertAlmostEqual(pistol_x, rifle_x)
        self.assertAlmostEqual(pistol_y - rifle_y, 10.0)

    def test_machine_gun_pivot_is_lower_than_the_pistol(self):
        _, pistol_y = self._drawn_gun_position(DEFAULT_GUN_ID)
        _, machine_gun_y = self._drawn_gun_position(MACHINE_GUN_GUN_ID)

        self.assertAlmostEqual(
            pistol_y - machine_gun_y,
            battle_scene.GUN_PIVOT_Y_OFFSETS[MACHINE_GUN_GUN_ID],
        )

    def test_machine_gun_horizontal_pivot_is_unchanged(self):
        pistol_x, _ = self._drawn_gun_position(DEFAULT_GUN_ID)
        machine_gun_x, _ = self._drawn_gun_position(MACHINE_GUN_GUN_ID)

        self.assertAlmostEqual(pistol_x, machine_gun_x)

    def test_overheated_gun_is_rendered_blue(self):
        self.scene.gun.overheated = True
        self.scene.gun.temperature = self.scene.gun.temperature_limit

        calls = self._draw_with_calls()

        self.assertEqual(
            calls,
            [
                ("gun-texture", *battle_scene.GUN_OVERHEAT_TINT),
                ("gun-texture", 255, 255, 255),
            ],
        )
        self.assertEqual(len(self.gun_image.composite_draws), 1)

    def test_gun_below_the_heat_range_is_rendered_white(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = (
            self.scene.gun.temperature_limit
            * battle_scene.GUN_HEAT_TINT_START_RATIO
            - 10
        )

        calls = self._draw_with_calls()

        self.assertEqual(calls[0], ("gun-texture", 255, 255, 255))

    def test_gun_is_white_at_the_start_of_the_heat_range(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = (
            self.scene.gun.temperature_limit
            * battle_scene.GUN_HEAT_TINT_START_RATIO
        )

        calls = self._draw_with_calls()

        self.assertEqual(calls[0], ("gun-texture", 255, 255, 255))

    def test_gun_reddens_gradually_as_the_temperature_rises(self):
        colors = []
        for ratio in (0.5, 0.625, 0.75, 0.875, 0.99):
            self.scene.gun.overheated = False
            self.scene.gun.temperature = self.scene.gun.temperature_limit * ratio
            colors.append(self.scene._gun_tint_color())

        self.assertEqual(colors[0], (255, 255, 255))
        for color in colors:
            self.assertEqual(color[0], 255)
        greens = [color[1] for color in colors]
        blues = [color[2] for color in colors]
        self.assertEqual(greens, sorted(greens, reverse=True))
        self.assertEqual(blues, sorted(blues, reverse=True))
        self.assertGreater(greens[0], greens[-1])
        self.assertLess(greens[-1], 100)

    def test_gun_at_the_limit_uses_the_full_red_tint(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = self.scene.gun.temperature_limit

        self.assertEqual(
            self.scene._gun_tint_color(),
            battle_scene.GUN_HEAT_TINT_COLOR,
        )

    def test_heat_tint_starts_at_half_of_each_gun_limit(self):
        gun = Gun.from_gun_id(MACHINE_GUN_GUN_ID)
        self.scene.gun = gun
        half_limit = gun.temperature_limit / 2

        gun.overheated = False
        gun.temperature = half_limit - 1
        self.assertEqual(self.scene._gun_tint_color(), battle_scene.GUN_WHITE_TINT)

        gun.temperature = half_limit
        self.assertEqual(self.scene._gun_tint_color(), battle_scene.GUN_WHITE_TINT)

        gun.temperature = half_limit + 1
        self.assertNotEqual(
            self.scene._gun_tint_color(),
            battle_scene.GUN_WHITE_TINT,
        )

    def test_overheat_switches_the_tint_to_blue(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = self.scene.gun.temperature_limit - 1
        self.assertNotEqual(
            self.scene._gun_tint_color(),
            battle_scene.GUN_OVERHEAT_TINT,
        )

        self.scene.gun.overheated = True

        self.assertEqual(
            self.scene._gun_tint_color(),
            battle_scene.GUN_OVERHEAT_TINT,
        )

    def test_hot_gun_tint_is_restored_after_drawing(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = self.scene.gun.temperature_limit - 1

        calls = self._draw_with_calls()

        self.assertNotEqual(calls[0], ("gun-texture", 255, 255, 255))
        self.assertEqual(calls[-1], ("gun-texture", 255, 255, 255))

    def test_tint_is_restored_even_if_drawing_fails(self):
        self.scene.gun.overheated = False
        self.scene.gun.temperature = self.scene.gun.temperature_limit - 1
        self.gun_image.composite_draw = mock.Mock(side_effect=RuntimeError("boom"))
        calls = []

        with mock.patch.object(
            battle_scene.pico2d,
            "SDL_SetTextureColorMod",
            side_effect=lambda *args: calls.append(args),
        ):
            with self.assertRaises(RuntimeError):
                self._draw_scene()

        self.assertEqual(calls[-1], ("gun-texture", 255, 255, 255))

    def test_gun_without_texture_draws_without_tinting(self):
        self.scene.gun.overheated = True
        textureless = FakeGunImage(texture=None)
        self.scene.gun_image = textureless

        with mock.patch.object(
            battle_scene.pico2d,
            "SDL_SetTextureColorMod",
        ) as set_color_mod:
            self._draw_scene()

        set_color_mod.assert_not_called()
        self.assertEqual(len(textureless.composite_draws), 1)


class BattleSceneGunRecoilTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.scene.gun_image = FakeGunImage()
        self.scene.player.image = FakeImage()

    def tearDown(self):
        game_world.clear()

    def _aim_right_and_fire(self):
        self.scene.mouse_screen_x = SCREEN_WIDTH / 2 + 100
        self.scene.mouse_screen_y = SCREEN_HEIGHT / 2
        self.scene.mouse_down("left")
        self.scene.update(0.0)

    def test_firing_starts_the_recoil_animation(self):
        self.assertEqual(self.scene.gun_recoil_remaining, 0.0)

        self._aim_right_and_fire()

        self.assertEqual(
            self.scene.gun_recoil_remaining,
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS,
        )

    def test_recoil_offset_shrinks_as_the_timer_runs_out(self):
        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )
        self.assertAlmostEqual(
            self.scene._gun_recoil_offset(),
            battle_scene.GUN_RECOIL_DISTANCE,
        )

        self.scene._update_gun_recoil(
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS / 2
        )

        self.assertAlmostEqual(
            self.scene.gun_recoil_remaining,
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS / 2,
        )
        self.assertAlmostEqual(
            self.scene._gun_recoil_offset(),
            battle_scene.GUN_RECOIL_DISTANCE * 0.25,
        )

    def test_recoil_returns_to_rest_after_the_recovery_time(self):
        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )

        self.scene._update_gun_recoil(
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )

        self.assertEqual(self.scene.gun_recoil_remaining, 0.0)
        self.assertEqual(self.scene._gun_recoil_offset(), 0.0)

    def test_recoil_timer_does_not_go_negative(self):
        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )

        self.scene._update_gun_recoil(
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS * 2
        )

        self.assertEqual(self.scene.gun_recoil_remaining, 0.0)

    def test_gun_has_no_recoil_offset_before_firing(self):
        self.assertEqual(self.scene._gun_recoil_offset(), 0.0)

    def test_recoil_pushes_the_gun_away_from_the_muzzle(self):
        self.scene.gun_image = FakeGunImage(texture=None)
        self.scene.player.set_screen_position(500, 500)
        self.scene.player.aim_angle = 0.0
        self.scene._draw_gun()
        rest_x, rest_y = self.scene.gun_image.composite_draws[-1][2:4]

        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )
        self.scene._draw_gun()
        recoil_x, recoil_y = self.scene.gun_image.composite_draws[-1][2:4]

        self.assertAlmostEqual(
            rest_x - recoil_x,
            battle_scene.GUN_RECOIL_DISTANCE,
        )
        self.assertAlmostEqual(recoil_y, rest_y)

    def test_recoil_pushes_the_gun_backwards_for_any_aim_direction(self):
        self.scene.gun_image = FakeGunImage(texture=None)
        self.scene.player.set_screen_position(500, 500)
        self.scene.player.aim_angle = math.pi / 2
        self.scene._draw_gun()
        rest_x, rest_y = self.scene.gun_image.composite_draws[-1][2:4]

        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )
        self.scene._draw_gun()
        recoil_x, recoil_y = self.scene.gun_image.composite_draws[-1][2:4]

        self.assertAlmostEqual(recoil_x, rest_x)
        self.assertAlmostEqual(
            rest_y - recoil_y,
            battle_scene.GUN_RECOIL_DISTANCE,
        )

    def test_reset_map_clears_the_recoil(self):
        self.scene.gun_recoil_remaining = (
            battle_scene.GUN_RECOIL_RECOVERY_SECONDS
        )

        self.scene.reset_map()

        self.assertEqual(self.scene.gun_recoil_remaining, 0.0)


class BattleSceneRecordTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_elapsed_time_accumulates_while_active(self):
        self.scene.update(0.1)

        self.scene.update(0.2)

        self.assertAlmostEqual(self.scene.elapsed_time, 0.3)

    def test_pausing_stops_the_clock(self):
        self.scene.update(0.1)

        self.scene.key_down("escape")
        self.scene.update(5.0)

        self.assertAlmostEqual(self.scene.elapsed_time, 0.1)

    def test_victory_records_the_clear_time(self):
        self.scene.waves_cleared = True

        self.scene.update(0.25)

        self.assertIs(self.scene.result, BattleResult.VICTORY)
        self.assertAlmostEqual(self.scene.clear_time, 0.25)

    def test_defeat_does_not_record_a_clear_time(self):
        self.scene.update(0.1)
        self.scene.player.hp = 0

        self.scene.update(0.2)

        self.assertIs(self.scene.result, BattleResult.DEFEAT)
        self.assertIsNone(self.scene.clear_time)
        self.assertAlmostEqual(self.scene.elapsed_time, 0.3)

    def test_quitting_keeps_the_reached_wave(self):
        self.scene.reached_wave = 4

        self.scene.key_down("escape")
        self.scene.key_down("s")
        self.scene.key_up("s")
        self.scene.key_down("space")

        self.assertIs(self.scene.result, BattleResult.QUIT)
        self.assertEqual(self.scene.reached_wave, 4)
        self.assertIsNone(self.scene.clear_time)

    def test_reset_map_clears_record_values(self):
        self.scene.elapsed_time = 30.0
        self.scene.reached_wave = 9
        self.scene.clear_time = 30.0

        self.scene.reset_map()

        self.assertEqual(self.scene.elapsed_time, 0.0)
        self.assertEqual(self.scene.reached_wave, 1)
        self.assertIsNone(self.scene.clear_time)

    def test_development_settings_configure_the_wave_director(self):
        scene = BattleScene(
            Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
            Gun(),
            FakeBackground(),
            hud_font=FakeFont(),
            enemy_images={enemy_type: FakeImage() for enemy_type in EnemyType},
            enemy_draw_rectangle=lambda *args: None,
            enemy_draw_circle=lambda *args: None,
            random_source=random.Random(0),
            total_waves=2,
            wave_spawn_rate=500,
        )

        self.assertEqual(scene.wave_director.total_waves, 2)
        self.assertEqual(scene.wave_director.spawn_rate, 500)

        scene.reset_map()

        self.assertEqual(scene.wave_director.total_waves, 2)
        self.assertEqual(scene.wave_director.spawn_rate, 500)


if __name__ == "__main__":
    unittest.main()
