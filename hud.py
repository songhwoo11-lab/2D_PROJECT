"""HUD rendering using the configured game font."""

import ctypes

import pico2d

from game_config import SCREEN_WIDTH


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


def _draw_centered_text(font, y, text):
    x = (SCREEN_WIDTH - _measure_text_width(font, text)) / 2
    font.draw(x, y, text, (255, 255, 255))


def draw_hud(player, gun, font, draw_rectangle):
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

    _draw_centered_text(
        font,
        60,
        "AMMO {}/{}".format(gun.magazine_ammo, gun.reserve_ammo),
    )
    _draw_centered_text(
        font,
        35,
        "MODE: {}".format(gun.fire_mode.value.upper()),
    )
    if gun.reloading:
        _draw_centered_text(font, 10, "RELOAD")
