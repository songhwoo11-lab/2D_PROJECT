"""HUD rendering using the configured game font."""

import ctypes
import math

import pico2d

from game_config import (
    HUD_FONT_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOTAL_WAVES,
    UI_SCALE,
)


TEMPERATURE_BAR_WIDTH = 200 * UI_SCALE
TEMPERATURE_BAR_HEIGHT = HUD_FONT_SIZE
HP_BAR_WIDTH = 200 * UI_SCALE
HP_BAR_HEIGHT = HUD_FONT_SIZE
TEMPERATURE_WARNING_THRESHOLD = 160.0
TEMPERATURE_WARNING_RED_THRESHOLD = 180.0
TEMPERATURE_WARNING_TEXT = "WARNING!"
TEMPERATURE_WARNING_YELLOW_COLOR = (255, 225, 90)
TEMPERATURE_WARNING_RED_COLOR = (255, 70, 60)
OVERHEAT_COLOR = (255, 70, 60)
HP_TRAIL_COLOR = (245, 150, 80)
DAMAGE_REDUCTION_COLOR = (255, 120, 100)
DAMAGE_REDUCTION_TIME_GAP = 12 * UI_SCALE
HUD_MARGIN = 20 * UI_SCALE
HUD_ROW_LOW = 55 * UI_SCALE
HUD_ROW_HIGH = 85 * UI_SCALE
HUD_AMMO_Y = 60 * UI_SCALE
HUD_MODE_Y = 35 * UI_SCALE
HUD_RELOAD_Y = 10 * UI_SCALE
HUD_WAVE_Y = SCREEN_HEIGHT - 25 * UI_SCALE
HUD_REMAINING_ENEMIES_Y = HUD_WAVE_Y - 25 * UI_SCALE


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


def _draw_right_text(font, y, text, color=(255, 255, 255)):
    x = SCREEN_WIDTH - HUD_MARGIN - _measure_text_width(font, text)
    font.draw(x, y, text, color)
    return x


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


def remaining_enemies_text(count):
    return "ENEMIES LEFT {}".format(count)


def coin_text(coins):
    return "COINS {}".format(coins)


def fire_status_text(gun):
    if gun.fire_blocked:
        return "OVERHEAT"
    return None


def temperature_warning_color(gun):
    if gun.temperature >= gun.temperature_limit:
        return None
    if gun.temperature >= TEMPERATURE_WARNING_RED_THRESHOLD:
        return TEMPERATURE_WARNING_RED_COLOR
    if gun.temperature >= TEMPERATURE_WARNING_THRESHOLD:
        return TEMPERATURE_WARNING_YELLOW_COLOR
    return None


def damage_reduction_text(gun):
    percent = round(gun.damage_reduction * 100)
    if percent <= 0:
        return None
    return "DMG -{}%".format(percent)


def damage_reduction_time_text(gun):
    remaining = gun.damage_reduction_remaining
    if remaining <= 0:
        return None
    total_seconds = math.ceil(remaining)
    minutes, seconds = divmod(total_seconds, 60)
    return "{:02d}:{:02d}".format(minutes, seconds)


def _draw_gauge_centered_text(font, bar_left, bar_bottom, text, color):
    x = bar_left + (
        TEMPERATURE_BAR_WIDTH - _measure_text_width(font, text)
    ) / 2
    font.draw(
        x,
        bar_bottom + TEMPERATURE_BAR_HEIGHT / 2,
        text,
        color,
    )


def _draw_temperature(font, gun, draw_rectangle):
    bar_left = SCREEN_WIDTH - HUD_MARGIN - TEMPERATURE_BAR_WIDTH
    bar_bottom = HUD_MARGIN
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
    _draw_right_text(font, HUD_ROW_LOW, temperature_text(gun))
    reduction_text = damage_reduction_text(gun)
    if reduction_text is not None:
        reduction_x = _draw_right_text(
            font,
            HUD_ROW_HIGH,
            reduction_text,
            DAMAGE_REDUCTION_COLOR,
        )
        time_text = damage_reduction_time_text(gun)
        if time_text is not None:
            time_x = (
                reduction_x
                - DAMAGE_REDUCTION_TIME_GAP
                - _measure_text_width(font, time_text)
            )
            font.draw(
                time_x,
                HUD_ROW_HIGH,
                time_text,
                DAMAGE_REDUCTION_COLOR,
            )
    status = fire_status_text(gun)
    if status is not None:
        _draw_gauge_centered_text(
            font,
            bar_left,
            bar_bottom,
            status,
            OVERHEAT_COLOR,
        )
    else:
        warning_color = temperature_warning_color(gun)
        if warning_color is not None:
            _draw_gauge_centered_text(
                font,
                bar_left,
                bar_bottom,
                TEMPERATURE_WARNING_TEXT,
                warning_color,
            )


def draw_hud(
    player,
    gun,
    font,
    draw_rectangle,
    wave=None,
    total_waves=TOTAL_WAVES,
    coins=None,
    remaining_enemies=None,
):
    hp_bar_left = HUD_MARGIN
    hp_bar_bottom = HUD_MARGIN
    hp_bar_width = HP_BAR_WIDTH
    hp_bar_height = HP_BAR_HEIGHT
    hp_ratio = min(max(player.hp / player.max_hp, 0.0), 1.0)
    hp_trail = getattr(player, "hp_trail", None)
    hp_trail_ratio = (
        hp_ratio
        if hp_trail is None
        else min(max(hp_trail.value / player.max_hp, 0.0), 1.0)
    )

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
        hp_bar_left + hp_bar_width * hp_trail_ratio,
        hp_bar_bottom + hp_bar_height,
        *HP_TRAIL_COLOR,
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
    font.draw(
        HUD_MARGIN,
        HUD_ROW_LOW,
        "HP {}/{}".format(player.hp, player.max_hp),
        (255, 255, 255),
    )
    if coins is not None:
        font.draw(HUD_MARGIN, HUD_ROW_HIGH, coin_text(coins), (255, 220, 100))

    ammo_text = (
        "AMMO INF"
        if gun.infinite_ammo
        else "AMMO {}/{}".format(gun.magazine_ammo, gun.reserve_ammo)
    )
    _draw_centered_text(font, HUD_AMMO_Y, ammo_text)
    _draw_centered_text(
        font,
        HUD_MODE_Y,
        "MODE: {}".format(gun.fire_mode.value.upper()),
    )
    if gun.reloading:
        _draw_centered_text(font, HUD_RELOAD_Y, "RELOAD")
    _draw_temperature(font, gun, draw_rectangle)
    if wave is not None:
        _draw_centered_text(font, HUD_WAVE_Y, wave_text(wave, total_waves))
    if remaining_enemies is not None:
        _draw_centered_text(
            font,
            HUD_REMAINING_ENEMIES_Y,
            remaining_enemies_text(remaining_enemies),
        )
