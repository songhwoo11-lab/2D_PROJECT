import unittest

from audio import (
    AudioManager,
    DEFAULT_VOLUME,
    LOBBY_MUSIC_FILE,
    MAX_VOLUME,
    SHOP_MUSIC_FILE,
    MIN_VOLUME,
    clamp_volume,
    to_mixer_volume,
)


class FakeMusic:
    def __init__(self):
        self.volumes = []
        self.repeat_count = 0
        self.stop_count = 0

    def set_volume(self, volume):
        self.volumes.append(volume)

    def repeat_play(self):
        self.repeat_count += 1

    def stop(self):
        self.stop_count += 1


class VolumeConversionTests(unittest.TestCase):
    def test_default_volume_is_fifty(self):
        self.assertEqual(DEFAULT_VOLUME, 50)

    def test_volume_range_is_zero_to_one_hundred(self):
        self.assertEqual((MIN_VOLUME, MAX_VOLUME), (0, 100))

    def test_clamp_volume_keeps_values_inside_the_range(self):
        self.assertEqual(clamp_volume(-1), 0)
        self.assertEqual(clamp_volume(50), 50)
        self.assertEqual(clamp_volume(101), 100)

    def test_music_volume_is_scaled_to_sdl_mixer_range(self):
        self.assertEqual(to_mixer_volume(0), 0)
        self.assertEqual(to_mixer_volume(50), 64)
        self.assertEqual(to_mixer_volume(100), 128)


class AudioManagerTests(unittest.TestCase):
    def setUp(self):
        self.music = FakeMusic()
        self.paths = []

        def loader(path):
            self.paths.append(path)
            return self.music

        self.manager = AudioManager(loader=loader)

    def test_new_manager_uses_the_default_volume(self):
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

    def test_same_track_is_not_restarted(self):
        self.manager.play(LOBBY_MUSIC_FILE)
        self.manager.play(LOBBY_MUSIC_FILE)

        self.assertEqual(len(self.paths), 1)
        self.assertEqual(self.music.repeat_count, 1)

    def test_changing_volume_applies_to_the_playing_track(self):
        self.manager.play(LOBBY_MUSIC_FILE)

        self.assertEqual(self.manager.set_volume(25), 25)

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

        self.manager.set_volume(100)

        self.assertEqual(self.music.volumes[-1], 128)
        self.assertEqual(second_music.volumes[-1], 128)

    def test_volume_changes_are_clamped(self):
        self.assertEqual(self.manager.change_volume(10), 60)
        self.assertEqual(self.manager.set_volume(1000), 100)
        self.assertEqual(self.manager.set_volume(-1000), 0)

    def test_stop_halts_the_playing_track(self):
        self.manager.play(LOBBY_MUSIC_FILE)

        self.manager.stop()

        self.assertEqual(self.music.stop_count, 1)
        self.assertIsNone(self.manager.current_music_name)

    def test_loader_failure_is_handled_without_raising(self):
        def failing_loader(path):
            raise OSError("no audio device")

        manager = AudioManager(loader=failing_loader)

        self.assertFalse(manager.play(LOBBY_MUSIC_FILE))
        self.assertIsNone(manager.current_music_name)

    def test_play_without_a_loader_is_a_no_op(self):
        manager = AudioManager()

        self.assertFalse(manager.play(LOBBY_MUSIC_FILE))
