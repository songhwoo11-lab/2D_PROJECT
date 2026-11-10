"""HUD rendering using the configured game font."""

import ctypes

import pico2d

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH, TOTAL_WAVES


TEMPERATURE_BAR_WIDTH = 200
TEMPERATURE_BAR_HEIGHT = 8


def _measure_text_width(font, text):
    width = ctypes.c_int()
    height = ctypes.c_int()
    result = pico2d.TTF_SizeUTF8(
        font.font,
        text.encode("utf-8"),
        ctypes.byref(width),
        ctypes.byref(height),
    )
    if result != 0:
        raise RuntimeError("Unable to measure HUD text: {!r}".format(text))
    return width.value


def _draw_centered_text(font, y, text, color=(255, 255, 255)):
    x = (SCREEN_WIDTH - _measure_text_width(font, text)) / 2
    font.draw(x, y, text, color)


def draw_centered_text(font, y, text, color=(255, 255, 255)):
    """Draw text horizontally centered on the screen."""
    _draw_centered_text(font, y, text, color)


def temperature_text(gun):
    return "TEMP {0:.0f}/{1:.0f}".format(
        gun.temperature,
        gun.temperature_limit,
    )


def wave_text(wave, total=TOTAL_WAVES):
    return "WAVE {}/{}".format(wave, total)


def fire_status_text(gun):
    if gun.fire_blocked:
        return "OVERHEAT"
    if gun.can_fire:
        return "READY"
    return None


def _draw_temperature(font, gun, draw_rectangle):
    bar_left = (SCREEN_WIDTH - TEMPERATURE_BAR_WIDTH) / 2
    bar_bottom = 95
    ratio = min(
        max(gun.temperature / gun.temperature_limit, 0.0),
        1.0,
    )
    draw_rectangle(
        bar_left,
        bar_bottom,
        bar_left + TEMPERATURE_BAR_WIDTH,
        bar_bottom + TEMPERATURE_BAR_HEIGHT,
        55,
        45,
        45,
        255,
        True,
    )
    draw_rectangle(
        bar_left,
        bar_bottom,
        bar_left + TEMPERATURE_BAR_WIDTH * ratio,
        bar_bottom + TEMPERATURE_BAR_HEIGHT,
        230,
        140,
        40,
        255,
        True,
    )
    _draw_centered_text(font, 85, temperature_text(gun))
    status = fire_status_text(gun)
    if status is not None:
        _draw_centered_text(font, 110, status)


def draw_hud(player, gun, font, draw_rectangle, wave=None, total_waves=TOTAL_WAVES):
    hp_bar_left = 20
    hp_bar_bottom = 20
    hp_bar_width = 200
    hp_bar_height = 10
    hp_ratio = min(max(player.hp / player.max_hp, 0.0), 1.0)

    draw_rectangle(
        hp_bar_left,
        hp_bar_bottom,
        hp_bar_left + hp_bar_width,
        hp_bar_bottom + hp_bar_height,
        55,
        45,
        45,
        255,
        True,
    )
    draw_rectangle(
        hp_bar_left,
        hp_bar_bottom,
        hp_bar_left + hp_bar_width * hp_ratio,
        hp_bar_bottom + hp_bar_height,
        220,
        45,
        45,
        255,
        True,
    )
    font.draw(20, 45, "HP {}/{}".format(player.hp, player.max_hp), (255, 255, 255))

    ammo_text = (
        "AMMO INF"
        if gun.infinite_ammo
        else "AMMO {}/{}".format(gun.magazine_ammo, gun.reserve_ammo)
    )
    _draw_centered_text(font, 60, ammo_text)
    _draw_centered_text(
        font,
        35,
        "MODE: {}".format(gun.fire_mode.value.upper()),
    )
    if gun.reloading:
        _draw_centered_text(font, 10, "RELOAD")
    _draw_temperature(font, gun, draw_rectangle)
    if wave is not None:
        _draw_centered_text(font, SCREEN_HEIGHT - 25, wave_text(wave, total_waves))
