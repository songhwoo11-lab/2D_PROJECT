from array import array
from pathlib import Path
import tempfile
import unittest
import wave

from audio import (
    AudioManager,
    BATTLE_MUSIC_FILE,
    BATTLE_PORTAL_EXIT_SOUND_FILE,
    BGM_VOLUME_FILES,
    DEFAULT_VOLUME,
    DEFEAT_MUSIC_FILE,
    LOBBY_MUSIC_FILE,
    LOBBY_PORTAL_ENTRY_SOUND_FILE,
    LOBBY_TO_BATTLE_SOUND_FILE,
    MACHINE_GUN_SHOT_SOUND_FILE,
    MAX_VOLUME,
    OVERHEAT_SOUND_FILE,
    RECORDS_MUSIC_FILE,
    SFX_VOLUME_FILES,
    SHOP_MUSIC_FILE,
    MIN_VOLUME,
    PISTOL_SHOT_SOUND_FILE,
    RELOAD_SOUND_FILE,
    RIFLE_SHOT_SOUND_FILE,
    TRAINING_MUSIC_FILE,
    VICTORY_MUSIC_FILE,
    MUSIC_BY_SCENE,
    clamp_volume,
    to_mixer_volume,
)


class FakeMusic:
    def __init__(self):
        self.volumes = []
        self.repeat_count = 0
        self.play_counts = []
        self.stop_count = 0
        self.pause_count = 0
        self.resume_count = 0

    def set_volume(self, volume):
        self.volumes.append(volume)

    def repeat_play(self):
        self.repeat_count += 1

    def play(self, loops=None):
        self.play_counts.append(loops)

    def stop(self):
        self.stop_count += 1

    def pause(self):
        self.pause_count += 1

    def resume(self):
        self.resume_count += 1


class FakeWav:
    def __init__(self):
        self.play_count = 0
        self.volumes = []

    def play(self):
        self.play_count += 1

    def set_volume(self, volume):
        self.volumes.append(volume)


class FakeChannelWav:
    def __init__(self):
        self.wav = object()
        self.volumes = []

    def set_volume(self, volume):
        self.volumes.append(volume)

    def play(self):
        raise AssertionError("channel playback should be used")


class FakeChannelControls:
    def __init__(self, max_channels=None):
        self.events = []
        self.playing = set()
        self.next_channel = 3
        self.max_channels = max_channels

    def play(self, sound):
        if self.max_channels is not None and len(self.playing) >= self.max_channels:
            self.events.append(("play_failed",))
            return -1
        channel = self.next_channel
        self.next_channel += 1
        self.events.append(("play", channel))
        self.playing.add(channel)
        return channel

    def pause(self, channel):
        self.events.append(("pause", channel))

    def resume(self, channel):
        self.events.append(("resume", channel))

    def is_playing(self, channel):
        return channel in self.playing

    def stop(self, channel):
        self.events.append(("stop", channel))
        self.playing.discard(channel)


class VolumeConversionTests(unittest.TestCase):
    def test_default_volume_is_fifty(self):
        self.assertEqual(DEFAULT_VOLUME, 50)

    def test_volume_range_is_zero_to_one_hundred(self):
        self.assertEqual((MIN_VOLUME, MAX_VOLUME), (0, 100))

    def test_battle_music_is_not_started_by_the_scene_mapping(self):
        self.assertNotIn("battle", MUSIC_BY_SCENE)

    def test_clamp_volume_keeps_values_inside_the_range(self):
        self.assertEqual(clamp_volume(-1), 0)
        self.assertEqual(clamp_volume(50), 50)
        self.assertEqual(clamp_volume(101), 100)

    def test_music_volume_is_scaled_to_sdl_mixer_range(self):
        self.assertEqual(to_mixer_volume(0), 0)
        self.assertEqual(to_mixer_volume(50), 64)
        self.assertEqual(to_mixer_volume(100), 128)

    def test_volume_groups_cover_the_requested_files(self):
        self.assertEqual(
            BGM_VOLUME_FILES,
            {
                BATTLE_MUSIC_FILE,
                LOBBY_MUSIC_FILE,
                RECORDS_MUSIC_FILE,
                SHOP_MUSIC_FILE,
                TRAINING_MUSIC_FILE,
            },
        )
        self.assertTrue(
            {
                RELOAD_SOUND_FILE,
                LOBBY_PORTAL_ENTRY_SOUND_FILE,
                LOBBY_TO_BATTLE_SOUND_FILE,
                BATTLE_MUSIC_FILE,
                DEFEAT_MUSIC_FILE,
                MACHINE_GUN_SHOT_SOUND_FILE,
                BATTLE_PORTAL_EXIT_SOUND_FILE,
                OVERHEAT_SOUND_FILE,
                PISTOL_SHOT_SOUND_FILE,
                RIFLE_SHOT_SOUND_FILE,
                VICTORY_MUSIC_FILE,
            }.issubset(SFX_VOLUME_FILES)
        )


class AudioManagerTests(unittest.TestCase):
    def setUp(self):
        self.music = FakeMusic()
        self.wav = FakeWav()
        self.paths = []
        self.sound_paths = []

        def loader(path):
            self.paths.append(path)
            return self.music

        def sound_loader(path):
            self.sound_paths.append(path)
            return self.wav

        self.manager = AudioManager(loader=loader)
        self.manager.set_sound_loader(sound_loader)

    def tearDown(self):
        self.manager.close()

    def test_new_manager_uses_the_default_volumes(self):
        self.assertEqual(self.manager.music_volume, DEFAULT_VOLUME)
        self.assertEqual(self.manager.sound_volume, DEFAULT_VOLUME)
        self.assertEqual(self.manager.volume, DEFAULT_VOLUME)

    def test_playing_lobby_music_loads_the_requested_file(self):
        self.assertTrue(self.manager.play(LOBBY_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + LOBBY_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, LOBBY_MUSIC_FILE)
        self.assertEqual(self.music.repeat_count, 1)
        self.assertEqual(self.music.volumes, [64])

    def test_playing_shop_music_loads_the_requested_file(self):
        self.assertTrue(self.manager.play(SHOP_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + SHOP_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, SHOP_MUSIC_FILE)

    def test_playing_battle_music_loads_the_requested_file(self):
        self.assertTrue(self.manager.play(BATTLE_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + BATTLE_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, BATTLE_MUSIC_FILE)

    def test_playing_training_music_loads_the_requested_file(self):
        self.assertTrue(self.manager.play(TRAINING_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + TRAINING_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, TRAINING_MUSIC_FILE)

    def test_playing_defeat_music_loads_the_requested_file_once(self):
        self.assertTrue(self.manager.play_once(DEFEAT_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + DEFEAT_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, DEFEAT_MUSIC_FILE)
        self.assertEqual(self.music.play_counts, [0])
        self.assertEqual(self.music.repeat_count, 0)

    def test_playing_victory_music_loads_the_requested_file_once(self):
        self.assertTrue(self.manager.play_once(VICTORY_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + VICTORY_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, VICTORY_MUSIC_FILE)
        self.assertEqual(self.music.play_counts, [0])
        self.assertEqual(self.music.repeat_count, 0)

    def test_playing_records_music_loads_the_requested_file(self):
        self.assertTrue(self.manager.play(RECORDS_MUSIC_FILE))

        self.assertEqual(len(self.paths), 1)
        self.assertTrue(self.paths[0].endswith("sound\\" + RECORDS_MUSIC_FILE))
        self.assertEqual(self.manager.current_music_name, RECORDS_MUSIC_FILE)
        self.assertEqual(self.music.repeat_count, 1)

    def test_playing_a_sound_loads_the_requested_file_once_per_call(self):
        self.assertTrue(self.manager.play_sound(PISTOL_SHOT_SOUND_FILE))
        self.assertTrue(self.manager.play_sound(PISTOL_SHOT_SOUND_FILE))

        self.assertEqual(len(self.sound_paths), 1)
        self.assertTrue(
            self.sound_paths[0].endswith("sound\\" + PISTOL_SHOT_SOUND_FILE)
        )
        self.assertEqual(self.wav.play_count, 2)

    def test_playing_the_rifle_sound_loads_the_requested_mp3(self):
        self.assertTrue(self.manager.play_sound(RIFLE_SHOT_SOUND_FILE))

        self.assertEqual(len(self.sound_paths), 1)
        self.assertTrue(
            self.sound_paths[0].endswith("sound\\" + RIFLE_SHOT_SOUND_FILE)
        )
        self.assertEqual(self.wav.play_count, 1)

    def test_playing_the_machine_gun_sound_loads_the_requested_mp3(self):
        self.assertTrue(self.manager.play_sound(MACHINE_GUN_SHOT_SOUND_FILE))

        self.assertEqual(len(self.sound_paths), 1)
        self.assertTrue(
            self.sound_paths[0].endswith("sound\\" + MACHINE_GUN_SHOT_SOUND_FILE)
        )
        self.assertEqual(self.wav.play_count, 1)

    def test_playing_the_reload_sound_loads_the_requested_file(self):
        self.assertTrue(self.manager.play_sound(RELOAD_SOUND_FILE))

        self.assertEqual(len(self.sound_paths), 1)
        self.assertTrue(
            self.sound_paths[0].endswith("sound\\" + RELOAD_SOUND_FILE)
        )

    def test_music_and_sound_volumes_are_independent(self):
        self.manager.play(BATTLE_MUSIC_FILE)
        self.manager.play_sound(PISTOL_SHOT_SOUND_FILE)

        self.assertEqual(self.manager.set_music_volume(25), 25)
        self.assertEqual(self.wav.volumes, [64])

        self.assertEqual(self.manager.set_sound_volume(75), 75)
        self.assertEqual(self.music.volumes, [64, 32])
        self.assertEqual(self.wav.volumes, [64, 96])

    def test_sound_volume_changes_apply_to_loaded_sounds(self):
        self.manager.play_sound(PISTOL_SHOT_SOUND_FILE)

        self.assertEqual(self.manager.set_sound_volume(25), 25)

        self.assertEqual(self.wav.volumes, [64, 32])

    def test_looping_play_does_not_use_one_shot_playback(self):
        self.manager.play(BATTLE_MUSIC_FILE)

        self.assertEqual(self.music.repeat_count, 1)
        self.assertEqual(self.music.play_counts, [])

    def test_same_track_is_not_restarted(self):
        self.manager.play(LOBBY_MUSIC_FILE)
        self.manager.play(LOBBY_MUSIC_FILE)

        self.assertEqual(len(self.paths), 1)
        self.assertEqual(self.music.repeat_count, 1)

    def test_changing_music_volume_applies_to_the_playing_track(self):
        self.manager.play(LOBBY_MUSIC_FILE)

        self.assertEqual(self.manager.set_music_volume(25), 25)

        self.assertEqual(self.music.volumes, [64, 32])

    def test_changing_volume_applies_to_every_loaded_track(self):
        second_music = FakeMusic()
        original_loader = self.manager.loader

        def loader(path):
            if path.endswith(SHOP_MUSIC_FILE):
                return second_music
            return original_loader(path)

        self.manager.set_loader(loader)
        self.manager.play(LOBBY_MUSIC_FILE)
        self.manager.play(SHOP_MUSIC_FILE)

        self.manager.set_music_volume(100)

        self.assertEqual(self.music.volumes[-1], 128)
        self.assertEqual(second_music.volumes[-1], 128)

    def test_volume_changes_are_clamped(self):
        self.assertEqual(self.manager.change_music_volume(10), 60)
        self.assertEqual(self.manager.set_music_volume(1000), 100)
        self.assertEqual(self.manager.set_music_volume(-1000), 0)
        self.assertEqual(self.manager.change_sound_volume(10), 60)
        self.assertEqual(self.manager.set_sound_volume(1000), 100)
        self.assertEqual(self.manager.set_sound_volume(-1000), 0)

    def test_stop_halts_the_playing_track(self):
        self.manager.play(LOBBY_MUSIC_FILE)

        self.manager.stop()

        self.assertEqual(self.music.stop_count, 1)
        self.assertIsNone(self.manager.current_music_name)

    def test_pause_keeps_the_current_track_without_restarting_it(self):
        self.manager.play(TRAINING_MUSIC_FILE)

        self.assertTrue(self.manager.pause())

        self.assertEqual(self.music.pause_count, 1)
        self.assertEqual(self.music.stop_count, 0)
        self.assertEqual(self.music.repeat_count, 1)
        self.assertEqual(self.manager.current_music_name, TRAINING_MUSIC_FILE)
        self.assertTrue(self.manager.is_paused)

    def test_resume_continues_the_same_track_without_restarting_it(self):
        self.manager.play(TRAINING_MUSIC_FILE)
        self.manager.pause()

        self.assertTrue(self.manager.resume())

        self.assertEqual(self.music.resume_count, 1)
        self.assertEqual(self.music.repeat_count, 1)
        self.assertEqual(self.music.stop_count, 0)
        self.assertEqual(self.manager.current_music_name, TRAINING_MUSIC_FILE)
        self.assertFalse(self.manager.is_paused)

    def test_repeated_pause_and_resume_are_ignored(self):
        self.manager.play(TRAINING_MUSIC_FILE)

        self.assertTrue(self.manager.pause())
        self.assertFalse(self.manager.pause())
        self.assertTrue(self.manager.resume())
        self.assertFalse(self.manager.resume())

        self.assertEqual(self.music.pause_count, 1)
        self.assertEqual(self.music.resume_count, 1)

    def test_stopping_a_paused_track_clears_the_paused_state(self):
        self.manager.play(TRAINING_MUSIC_FILE)
        self.manager.pause()

        self.manager.stop()

        self.assertFalse(self.manager.is_paused)
        self.assertIsNone(self.manager.current_music_name)
        self.assertFalse(self.manager.resume())

    def test_loader_failure_is_handled_without_raising(self):
        def failing_loader(path):
            raise OSError("no audio device")

        manager = AudioManager(loader=failing_loader)

        self.assertFalse(manager.play(LOBBY_MUSIC_FILE))
        self.assertIsNone(manager.current_music_name)

    def test_play_without_a_loader_is_a_no_op(self):
        manager = AudioManager()

        self.assertFalse(manager.play(LOBBY_MUSIC_FILE))


class SoundChannelTests(unittest.TestCase):
    def setUp(self):
        self.controls = FakeChannelControls()
        self.wav = FakeChannelWav()
        self.manager = AudioManager(channel_controls=self.controls)
        self.manager.set_sound_loader(lambda path: self.wav)

    def tearDown(self):
        self.manager.close()

    def test_play_pause_resume_and_stop_use_the_same_channel(self):
        self.assertTrue(self.manager.play_sound(RELOAD_SOUND_FILE))

        self.assertEqual(self.controls.events, [("play", 3)])

        self.assertTrue(self.manager.pause_sound(RELOAD_SOUND_FILE))

        self.assertEqual(
            self.controls.events,
            [("play", 3), ("pause", 3)],
        )

        self.assertTrue(self.manager.resume_sound(RELOAD_SOUND_FILE))

        self.assertEqual(
            self.controls.events,
            [("play", 3), ("pause", 3), ("resume", 3)],
        )

        self.assertTrue(self.manager.stop_sound(RELOAD_SOUND_FILE))

        self.assertEqual(
            self.controls.events,
            [("play", 3), ("pause", 3), ("resume", 3), ("stop", 3)],
        )

        self.controls.events.clear()

        self.assertFalse(self.manager.pause_sound(RELOAD_SOUND_FILE))
        self.assertFalse(self.manager.resume_sound(RELOAD_SOUND_FILE))
        self.assertFalse(self.manager.stop_sound(RELOAD_SOUND_FILE))
        self.assertEqual(self.controls.events, [])

    def test_replaying_a_sound_replaces_the_previous_channel(self):
        self.manager.play_sound(RELOAD_SOUND_FILE)
        self.manager.play_sound(RELOAD_SOUND_FILE)

        self.assertTrue(self.manager.pause_sound(RELOAD_SOUND_FILE))

        self.assertEqual(
            self.controls.events,
            [("play", 3), ("stop", 3), ("play", 4), ("pause", 4)],
        )

    def test_rapid_replays_never_exhaust_the_channel_pool(self):
        controls = FakeChannelControls(max_channels=1)
        manager = AudioManager(channel_controls=controls)
        manager.set_sound_loader(lambda path: FakeChannelWav())

        for _ in range(10):
            self.assertTrue(manager.play_sound(RIFLE_SHOT_SOUND_FILE))

        self.assertEqual(len(controls.playing), 1)
        self.assertNotIn(("play_failed",), controls.events)
        manager.close()

    def test_channel_reused_by_another_sound_is_not_controlled(self):
        self.manager.play_sound(RELOAD_SOUND_FILE)
        self.controls.next_channel = 3
        self.manager.play_sound(PISTOL_SHOT_SOUND_FILE)

        self.assertFalse(self.manager.pause_sound(RELOAD_SOUND_FILE))
        self.assertFalse(self.manager.stop_sound(RELOAD_SOUND_FILE))
        self.assertEqual(self.controls.events, [("play", 3), ("play", 3)])

    def test_finished_channels_are_dropped(self):
        self.manager.play_sound(RELOAD_SOUND_FILE)
        self.controls.playing.clear()

        self.assertFalse(self.manager.pause_sound(RELOAD_SOUND_FILE))
        self.assertEqual(self.controls.events, [("play", 3)])

    def test_sound_objects_without_a_channel_still_play_normally(self):
        wav = FakeWav()
        manager = AudioManager(channel_controls=self.controls)
        manager.set_sound_loader(lambda path: wav)

        self.assertTrue(manager.play_sound(PISTOL_SHOT_SOUND_FILE))

        self.assertEqual(wav.play_count, 1)
        self.assertFalse(manager.pause_sound(PISTOL_SHOT_SOUND_FILE))
        self.assertFalse(manager.resume_sound(PISTOL_SHOT_SOUND_FILE))
        self.assertEqual(self.controls.events, [])
        manager.close()


class SoundTimingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.sound_directory = Path(self.directory.name)
        self.name = "timed.wav"
        self.framerate = 1000
        self.frame_count = 2205
        with wave.open(str(self.sound_directory / self.name), "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(self.framerate)
            wav.writeframes(
                array(
                    "h",
                    [index % 1000 for index in range(self.frame_count * 2)],
                ).tobytes()
            )
        self.paths = []
        self.wav = FakeWav()

        def sound_loader(path):
            self.paths.append(path)
            return self.wav

        self.manager = AudioManager(sound_directory=self.sound_directory)
        self.manager.set_sound_loader(sound_loader)

    def tearDown(self):
        self.manager.close()
        self.directory.cleanup()

    def loaded_duration(self, path):
        with wave.open(path, "rb") as wav:
            return wav.getnframes() / wav.getframerate()

    def test_target_duration_resamples_the_sound(self):
        target = 1.1025

        self.assertTrue(self.manager.play_sound(self.name, target_duration=target))

        self.assertEqual(len(self.paths), 1)
        self.assertNotEqual(Path(self.paths[0]), self.sound_directory / self.name)
        self.assertAlmostEqual(
            self.loaded_duration(self.paths[0]),
            target,
            delta=1 / self.framerate,
        )
        self.assertEqual(self.wav.play_count, 1)

    def test_same_target_duration_uses_the_cached_sound(self):
        self.manager.play_sound(self.name, target_duration=1.0)
        self.manager.play_sound(self.name, target_duration=1.0)

        self.assertEqual(len(self.paths), 1)
        self.assertEqual(self.wav.play_count, 2)

    def test_different_target_durations_are_loaded_separately(self):
        self.manager.play_sound(self.name, target_duration=1.0)
        self.manager.play_sound(self.name, target_duration=2.0)

        self.assertEqual(len(self.paths), 2)

    def test_default_playback_still_uses_the_original_file(self):
        self.manager.play_sound(self.name)

        self.assertEqual(len(self.paths), 1)
        self.assertEqual(Path(self.paths[0]), self.sound_directory / self.name)
