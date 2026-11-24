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

MUSIC_BY_SCENE = {
    "lobby": LOBBY_MUSIC_FILE,
    "shop": SHOP_MUSIC_FILE,
}


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

    @property
    def current_music_name(self):
        return self._current_name

    def set_loader(self, loader):
        """Set the function used to load music (pico2d.load_music in game)."""
        if loader is self.loader:
            return
        self.loader = loader
        self._music_cache.clear()
        self._current_music = None
        self._current_name = None

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
        if self._current_name == name and self._current_music is not None:
            return False
        self.stop()
        music = self._load(name)
        if music is None:
            return False
        try:
            music.repeat_play()
        except (OSError, RuntimeError):
            self._current_music = None
            self._current_name = None
            return False
        self._current_music = music
        self._current_name = name
        return True

    def stop(self):
        if self._current_music is not None:
            try:
                self._current_music.stop()
            except (OSError, RuntimeError):
                pass
        self._current_music = None
        self._current_name = None

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
