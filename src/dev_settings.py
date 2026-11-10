"""Optional environment overrides for quickly verifying battle flows."""

import os


WAVES_ENV = "CHALLENGING_GUNNER_WAVES"
SPAWN_RATE_ENV = "CHALLENGING_GUNNER_SPAWN_RATE"


def _read_environment(name, environ):
    source = os.environ if environ is None else environ
    value = source.get(name)
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def development_total_waves(environ=None):
    value = _read_environment(WAVES_ENV, environ)
    if value is None:
        return None
    try:
        waves = int(value)
    except ValueError:
        return None
    return waves if waves > 0 else None


def development_spawn_rate(environ=None):
    value = _read_environment(SPAWN_RATE_ENV, environ)
    if value is None:
        return None
    try:
        rate = float(value)
    except ValueError:
        return None
    return rate if rate > 0 else None
