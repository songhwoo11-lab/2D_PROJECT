"""Centralized music playback and volume settings."""

from pathlib import Path


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

MUSIC_BY_SCENE = {
    "lobby": LOBBY_MUSIC_FILE,
    "shop": SHOP_MUSIC_FILE,
}

# Battle and training music are controlled by their scenes so they start at
# the right point in each scene's intro.


def clamp_volume(volume):
    """Keep a setting inside the 0..100 range exposed by the settings menu."""
    return max(MIN_VOLUME, min(MAX_VOLUME, int(volume)))


def to_mixer_volume(volume):
    """Convert a 0..100 setting to SDL_mixer's 0..128 music volume."""
    return round(clamp_volume(volume) / MAX_VOLUME * MIXER_MAX_VOLUME)


class AudioManager:
    """Loads and plays music while applying one shared volume setting."""

    def __init__(self, loader=None, sound_directory=SOUND_DIRECTORY):
        self.loader = loader
        self.sound_directory = Path(sound_directory)
        self.volume = DEFAULT_VOLUME
        self._music_cache = {}
        self._current_music = None
        self._current_name = None
        self._paused = False

    @property
    def current_music_name(self):
        return self._current_name

    @property
    def is_paused(self):
        return self._paused

    def set_loader(self, loader):
        """Set the function used to load music (pico2d.load_music in game)."""
        if loader is self.loader:
            return
        self.loader = loader
        self._music_cache.clear()
        self._current_music = None
        self._current_name = None
        self._paused = False

    def set_volume(self, volume):
        """Apply a new 0..100 volume to every loaded and playing track."""
        self.volume = clamp_volume(volume)
        for music in self._music_cache.values():
            self._apply_volume(music)
        return self.volume

    def change_volume(self, amount):
        return self.set_volume(self.volume + amount)

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

    def _apply_volume(self, music):
        try:
            music.set_volume(to_mixer_volume(self.volume))
        except (OSError, RuntimeError):
            pass
