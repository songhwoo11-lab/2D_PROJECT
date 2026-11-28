"""Centralized music playback and volume settings."""

from array import array
from pathlib import Path
import math
import sys
import tempfile
import wave

import pico2d


DEFAULT_VOLUME = 50
MIN_VOLUME = 0
MAX_VOLUME = 100
VOLUME_STEP = 10

# SDL_mixer uses a 0..128 range for music volume.
MIXER_MAX_VOLUME = 128

SOUND_DIRECTORY = Path(__file__).resolve().parent.parent / "sound"
LOBBY_MUSIC_FILE = "lobby bgm.mp3"
SHOP_MUSIC_FILE = "shop bgm.mp3"
BATTLE_MUSIC_FILE = "battle.mp3"
TRAINING_MUSIC_FILE = "training.mp3"
DEFEAT_MUSIC_FILE = "lose game.mp3"
VICTORY_MUSIC_FILE = "win game.mp3"
RECORDS_MUSIC_FILE = "log check bgm.mp3"
PISTOL_SHOT_SOUND_FILE = "pistol shot sound.wav"
RIFLE_SHOT_SOUND_FILE = "rifle shot sound.mp3"
MACHINE_GUN_SHOT_SOUND_FILE = "machine gun shot sound.mp3"
RELOAD_SOUND_FILE = "gun reload sound.wav"
LOBBY_PORTAL_ENTRY_SOUND_FILE = "in lobby portal.mp3"
LOBBY_TO_BATTLE_SOUND_FILE = "lobby to portal.mp3"
BATTLE_PORTAL_EXIT_SOUND_FILE = "out battle portal.mp3"
OVERHEAT_SOUND_FILE = "overheat sound.mp3"

MUSIC_BY_SCENE = {
    "lobby": LOBBY_MUSIC_FILE,
    "shop": SHOP_MUSIC_FILE,
}

# Volume groups exposed by the settings panel. Battle music is also listed
# under effects because it can be reused as a one-shot, but while it is used
# as the looping battle track it follows the music volume.
BGM_VOLUME_FILES = frozenset(
    {
        BATTLE_MUSIC_FILE,
        LOBBY_MUSIC_FILE,
        RECORDS_MUSIC_FILE,
        SHOP_MUSIC_FILE,
        TRAINING_MUSIC_FILE,
    }
)
SFX_VOLUME_FILES = frozenset(
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
    }
)

# Battle and training music are controlled by their scenes so they start at
# the right point in each scene's intro.


def resample_wav_frames(frames, channels, speed):
    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()
    frame_count = len(samples) // channels
    if frame_count == 0:
        return b""
    output_frames = max(1, int(round(frame_count / speed)))
    resampled = array("h", [0]) * (output_frames * channels)
    for index in range(output_frames):
        position = index * speed
        left = min(int(position), frame_count - 1)
        right = min(left + 1, frame_count - 1)
        weight = position - left
        left_base = left * channels
        right_base = right * channels
        output_base = index * channels
        for channel in range(channels):
            value = samples[left_base + channel] * (1.0 - weight)
            value += samples[right_base + channel] * weight
            resampled[output_base + channel] = int(round(value))
    if sys.byteorder != "little":
        resampled.byteswap()
    return resampled.tobytes()


def clamp_volume(volume):
    """Keep a setting inside the 0..100 range exposed by the settings menu."""
    return max(MIN_VOLUME, min(MAX_VOLUME, int(volume)))


def to_mixer_volume(volume):
    """Convert a 0..100 setting to SDL_mixer's 0..128 music volume."""
    return round(clamp_volume(volume) / MAX_VOLUME * MIXER_MAX_VOLUME)


class Pico2dSoundChannels:
    def play(self, sound):
        return pico2d.Mix_PlayChannel(-1, sound.wav, 0)

    def pause(self, channel):
        pico2d.Mix_Pause(channel)

    def resume(self, channel):
        pico2d.Mix_Resume(channel)

    def is_playing(self, channel):
        return bool(pico2d.Mix_Playing(channel))

    def stop(self, channel):
        pico2d.Mix_HaltChannel(channel)


class AudioManager:
    """Loads and plays audio with separate music and effect volume settings."""

    def __init__(
        self, loader=None, sound_directory=SOUND_DIRECTORY, channel_controls=None
    ):
        self.loader = loader
        self.sound_loader = None
        self.sound_directory = Path(sound_directory)
        self.channel_controls = channel_controls or Pico2dSoundChannels()
        self.music_volume = DEFAULT_VOLUME
        self.sound_volume = DEFAULT_VOLUME
        self._music_cache = {}
        self._sound_cache = {}
        self._sound_channels = {}
        self._channel_owners = {}
        self._sound_temp_dir = None
        self._current_music = None
        self._current_name = None
        self._paused = False

    @property
    def current_music_name(self):
        return self._current_name

    @property
    def is_paused(self):
        return self._paused

    @property
    def volume(self):
        """Backward-compatible alias for the music volume."""
        return self.music_volume

    @volume.setter
    def volume(self, value):
        self.music_volume = clamp_volume(value)

    def set_loader(self, loader):
        """Set the function used to load music (pico2d.load_music in game)."""
        if loader is self.loader:
            return
        self.loader = loader
        self._music_cache.clear()
        self._current_music = None
        self._current_name = None
        self._paused = False

    def set_sound_loader(self, loader):
        """Set the loader used for short sound effects (pico2d.load_wav)."""
        if loader is self.sound_loader:
            return
        self.sound_loader = loader
        self._stop_all_sound_channels()
        self._sound_cache.clear()
        self._sound_channels.clear()
        self._channel_owners.clear()

    def set_music_volume(self, volume):
        """Apply a new 0..100 volume to background music."""
        self.music_volume = clamp_volume(volume)
        for music in self._music_cache.values():
            self._apply_volume(music)
        return self.music_volume

    def set_sound_volume(self, volume):
        """Apply a new 0..100 volume to sound effects."""
        self.sound_volume = clamp_volume(volume)
        for sound in self._sound_cache.values():
            self._apply_sound_volume(sound)
        return self.sound_volume

    def set_volume(self, volume):
        """Backward-compatible alias for set_music_volume()."""
        return self.set_music_volume(volume)

    def change_music_volume(self, amount):
        return self.set_music_volume(self.music_volume + amount)

    def change_sound_volume(self, amount):
        return self.set_sound_volume(self.sound_volume + amount)

    def change_volume(self, amount):
        """Backward-compatible alias for change_music_volume()."""
        return self.change_music_volume(amount)

    def play(self, name):
        """Loop the named track; return False when audio is unavailable."""
        return self._play_track(name, repeat=True)

    def play_once(self, name):
        """Play the named track once; return False when audio is unavailable."""
        return self._play_track(name, repeat=False)

    def _play_track(self, name, repeat):
        if self._current_name == name and self._current_music is not None:
            return False
        self.stop()
        music = self._load(name)
        if music is None:
            return False
        try:
            if repeat:
                music.repeat_play()
            else:
                # pico2d's default play(1) plays twice; 0 means one playback.
                music.play(0)
        except (OSError, RuntimeError):
            self._current_music = None
            self._current_name = None
            return False
        self._current_music = music
        self._current_name = name
        return True

    def play_sound(self, name, target_duration=None):
        """Play a short sound effect once; return False when audio is unavailable."""
        sound = self._load_sound(name, target_duration)
        if sound is None:
            return False
        try:
            if hasattr(sound, "wav"):
                # Keep one active channel per sound. Without this, automatic
                # fire can exhaust SDL_mixer's small channel pool and silence
                # both later shots and the reload sound.
                self._stop_tracked_sound(name)
                channel = self.channel_controls.play(sound)
                if channel is None or channel < 0:
                    return False
                self._sound_channels.setdefault(name, []).append(channel)
                self._channel_owners[channel] = name
            else:
                sound.play()
        except (OSError, RuntimeError):
            return False
        return True

    def pause_sound(self, name):
        return self._change_sound_playback(name, "pause")

    def resume_sound(self, name):
        return self._change_sound_playback(name, "resume")

    def stop_sound(self, name):
        channels = self._active_sound_channels(name)
        for channel in channels:
            try:
                self.channel_controls.stop(channel)
            except (OSError, RuntimeError):
                pass
            self._channel_owners.pop(channel, None)
        self._sound_channels[name] = []
        return bool(channels)

    def pause(self):
        """Pause the current track without losing its playback position."""
        if self._current_music is None or self._paused:
            return False
        try:
            self._current_music.pause()
        except (OSError, RuntimeError):
            return False
        self._paused = True
        return True

    def resume(self):
        """Resume a paused track from the position where it was paused."""
        if self._current_music is None or not self._paused:
            return False
        try:
            self._current_music.resume()
        except (OSError, RuntimeError):
            return False
        self._paused = False
        return True

    def close(self):
        self.stop()
        self._stop_all_sound_channels()
        self._sound_cache.clear()
        if self._sound_temp_dir is not None:
            self._sound_temp_dir.cleanup()
            self._sound_temp_dir = None

    def stop(self):
        if self._current_music is not None:
            try:
                self._current_music.stop()
            except (OSError, RuntimeError):
                pass
        self._current_music = None
        self._current_name = None
        self._paused = False

    def _load(self, name):
        if name in self._music_cache:
            return self._music_cache[name]
        if self.loader is None:
            return None
        try:
            music = self.loader(str(self.sound_directory / name))
        except (OSError, RuntimeError, ValueError):
            self.loader = None
            return None
        if music is None:
            return None
        self._apply_volume(music)
        self._music_cache[name] = music
        return music

    def _change_sound_playback(self, name, action):
        channels = self._active_sound_channels(name)
        for channel in channels:
            try:
                getattr(self.channel_controls, action)(channel)
            except (OSError, RuntimeError):
                pass
        return bool(channels)

    def _active_sound_channels(self, name):
        active = []
        for channel in self._sound_channels.get(name, []):
            if self._channel_owners.get(channel) != name:
                # SDL_mixer may have reused the channel for another sound.
                # Leave its new owner intact and only drop the stale mapping.
                continue
            try:
                playing = self.channel_controls.is_playing(channel)
            except (OSError, RuntimeError):
                playing = False
            if playing:
                active.append(channel)
            else:
                self._channel_owners.pop(channel, None)
        self._sound_channels[name] = active
        return active

    def _stop_tracked_sound(self, name):
        """Stop every channel still owned by this sound, including paused ones."""
        channels = []
        for channel in self._sound_channels.get(name, []):
            if self._channel_owners.get(channel) == name:
                channels.append(channel)
        for channel in channels:
            try:
                self.channel_controls.stop(channel)
            except (OSError, RuntimeError):
                pass
            self._channel_owners.pop(channel, None)
        self._sound_channels[name] = []
        return bool(channels)

    def _stop_all_sound_channels(self):
        for name in list(self._sound_channels):
            self._stop_tracked_sound(name)
        self._channel_owners.clear()

    @staticmethod
    def _sound_key(name, target_duration):
        duration = None
        if target_duration is not None:
            duration = round(float(target_duration), 6)
            if duration <= 0 or not math.isfinite(duration):
                duration = None
        return name, duration

    def _load_sound(self, name, target_duration=None):
        key = self._sound_key(name, target_duration)
        duration = key[1]
        if key in self._sound_cache:
            return self._sound_cache[key]
        if self.sound_loader is None:
            return None
        path = self.sound_directory / name
        if duration is not None:
            path = self._resampled_sound_path(name, duration)
        try:
            sound = self.sound_loader(str(path))
        except (OSError, RuntimeError, ValueError):
            self.sound_loader = None
            return None
        if sound is None:
            return None
        self._apply_sound_volume(sound)
        self._sound_cache[key] = sound
        return sound

    def _resampled_sound_path(self, name, duration):
        source_path = self.sound_directory / name
        try:
            with wave.open(str(source_path), "rb") as source:
                if source.getcomptype() != "NONE" or source.getsampwidth() != 2:
                    return source_path
                channels = source.getnchannels()
                framerate = source.getframerate()
                frame_count = source.getnframes()
                frames = source.readframes(frame_count)
        except (OSError, EOFError, wave.Error):
            return source_path
        if frame_count <= 0 or framerate <= 0 or channels <= 0:
            return source_path
        speed = frame_count / framerate / duration
        if speed <= 0 or not math.isfinite(speed):
            return source_path
        if self._sound_temp_dir is None:
            self._sound_temp_dir = tempfile.TemporaryDirectory(
                prefix="challenging-gunner-"
            )
        target_path = Path(self._sound_temp_dir.name) / "{}-{}.wav".format(
            Path(name).stem.replace(" ", "_"),
            str(duration).replace(".", "_"),
        )
        resampled = resample_wav_frames(frames, channels, speed)
        with wave.open(str(target_path), "wb") as target:
            target.setnchannels(channels)
            target.setsampwidth(2)
            target.setframerate(framerate)
            target.writeframes(resampled)
        return target_path

    def _apply_volume(self, music):
        try:
            music.set_volume(to_mixer_volume(self.music_volume))
        except (OSError, RuntimeError):
            pass

    def _apply_sound_volume(self, sound):
        try:
            sound.set_volume(to_mixer_volume(self.sound_volume))
        except (OSError, RuntimeError):
            pass
