import unittest
from types import SimpleNamespace
from unittest import mock

import hud
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import (
    coin_text,
    damage_reduction_text,
    damage_reduction_time_text,
    fire_status_text,
    remaining_enemies_text,
    temperature_text,
    wave_text,
)


def make_gun(**overrides):
    values = {
        "temperature": 10.0,
        "temperature_limit": 200.0,
        "fire_blocked": False,
        "can_fire": True,
        "reloading": False,
        "infinite_ammo": False,
        "magazine_ammo": 10,
        "reserve_ammo": 90,
        "fire_mode": SimpleNamespace(value="single"),
        "damage_reduction": 0.0,
        "damage_reduction_remaining": 0.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class TemperatureTextTests(unittest.TestCase):
    def test_temperature_text_shows_current_and_limit(self):
        gun = make_gun(temperature=42.4, temperature_limit=200.0)

        self.assertEqual(temperature_text(gun), "TEMP 42/200")


class WaveTextTests(unittest.TestCase):
    def test_wave_text_shows_current_and_total(self):
        self.assertEqual(wave_text(3, 30), "WAVE 3/30")

    def test_wave_text_defaults_to_thirty_waves(self):
        self.assertEqual(wave_text(7), "WAVE 7/30")


class CoinTextTests(unittest.TestCase):
    def test_coin_text_shows_the_current_balance(self):
        self.assertEqual(coin_text(123), "COINS 123")


class RemainingEnemiesTextTests(unittest.TestCase):
    def test_remaining_enemies_text_shows_the_count(self):
        self.assertEqual(remaining_enemies_text(12), "ENEMIES LEFT 12")

    def test_remaining_enemies_text_shows_zero(self):
        self.assertEqual(remaining_enemies_text(0), "ENEMIES LEFT 0")


class FireStatusTextTests(unittest.TestCase):
    def test_overheat_is_shown_when_blocked(self):
        gun = make_gun(fire_blocked=True, can_fire=False)

        self.assertEqual(fire_status_text(gun), "OVERHEAT")

    def test_ready_is_not_shown_when_gun_can_fire(self):
        gun = make_gun(can_fire=True)

        self.assertIsNone(fire_status_text(gun))

    def test_no_status_is_shown_during_fire_cooldown(self):
        gun = make_gun(can_fire=False, reloading=False)

        self.assertIsNone(fire_status_text(gun))

    def test_reloading_is_not_reported_as_ready_or_overheat(self):
        gun = make_gun(can_fire=False, reloading=True)

        self.assertIsNone(fire_status_text(gun))


class DamageReductionTextTests(unittest.TestCase):
    def test_no_damage_reduction_is_not_shown(self):
        self.assertIsNone(damage_reduction_text(make_gun()))

    def test_reduction_is_shown_as_a_percentage(self):
        gun = make_gun(damage_reduction=0.8)

        self.assertEqual(damage_reduction_text(gun), "DMG -80%")

    def test_reduction_is_rounded_to_a_whole_percentage(self):
        gun = make_gun(damage_reduction=0.404)

        self.assertEqual(damage_reduction_text(gun), "DMG -40%")

    def test_negligible_reduction_is_not_shown(self):
        gun = make_gun(damage_reduction=0.004)

        self.assertIsNone(damage_reduction_text(gun))


class DamageReductionTimeTextTests(unittest.TestCase):
    def test_full_duration_is_shown_as_one_and_a_half_minutes(self):
        gun = make_gun(damage_reduction_remaining=90.0)

        self.assertEqual(damage_reduction_time_text(gun), "01:30")

    def test_remaining_time_is_shown_as_minutes_and_seconds(self):
        gun = make_gun(damage_reduction_remaining=61.0)

        self.assertEqual(damage_reduction_time_text(gun), "01:01")

    def test_partial_seconds_round_up(self):
        gun = make_gun(damage_reduction_remaining=60.2)

        self.assertEqual(damage_reduction_time_text(gun), "01:01")

    def test_last_second_is_shown_as_one_second(self):
        gun = make_gun(damage_reduction_remaining=0.2)

        self.assertEqual(damage_reduction_time_text(gun), "00:01")

    def test_no_reduction_is_not_shown(self):
        gun = make_gun(damage_reduction_remaining=0.0)

        self.assertIsNone(damage_reduction_time_text(gun))


class RecordingFont:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, text, color=(255, 255, 255)):
        self.draws.append((x, y, text, color))


class HudLayoutTests(unittest.TestCase):
    TEXT_WIDTH = 60

    def _draw_hud(self, gun, player=None):
        font = RecordingFont()
        rectangles = []

        def draw_rectangle(x1, y1, x2, y2, r, g, b, a, filled):
            rectangles.append((x1, y1, x2, y2))

        if player is None:
            player = SimpleNamespace(hp=100, max_hp=100)
        with mock.patch.object(hud, "_measure_text_width", return_value=self.TEXT_WIDTH):
            hud.draw_hud(
                player,
                gun,
                font,
                draw_rectangle,
                wave=1,
                total_waves=30,
                coins=7,
                remaining_enemies=12,
            )
        return font, rectangles

    def _text_draw(self, font, text):
        for draw_call in font.draws:
            if draw_call[2] == text:
                return draw_call[:3]
        self.fail("text {!r} was not drawn".format(text))

    def _text_color(self, font, text):
        for draw_call in font.draws:
            if draw_call[2] == text:
                return draw_call[3]
        self.fail("text {!r} was not drawn".format(text))

    def test_temperature_bar_is_in_the_bottom_right_corner(self):
        gun = make_gun()

        _, rectangles = self._draw_hud(gun)

        bar = rectangles[3]
        self.assertEqual(
            bar,
            (
                SCREEN_WIDTH - hud.HUD_MARGIN - hud.TEMPERATURE_BAR_WIDTH,
                hud.HUD_MARGIN,
                SCREEN_WIDTH - hud.HUD_MARGIN,
                hud.HUD_MARGIN + hud.TEMPERATURE_BAR_HEIGHT,
            ),
        )

    def test_temperature_bar_thickness_matches_the_hud_font_size(self):
        gun = make_gun()

        _, rectangles = self._draw_hud(gun)

        x1, y1, x2, y2 = rectangles[3]
        self.assertEqual(y2 - y1, hud.HUD_FONT_SIZE)

    def test_hp_bar_thickness_matches_the_hud_font_size(self):
        gun = make_gun()

        _, rectangles = self._draw_hud(gun)

        x1, y1, x2, y2 = rectangles[0]
        self.assertEqual(y2 - y1, hud.HUD_FONT_SIZE)

    def test_hp_trailing_bar_follows_the_delayed_value(self):
        gun = make_gun()
        player = SimpleNamespace(
            hp=60,
            max_hp=100,
            hp_trail=SimpleNamespace(value=80.0),
        )

        _, rectangles = self._draw_hud(gun, player)

        background = rectangles[0]
        trailing = rectangles[1]
        current = rectangles[2]
        self.assertEqual(background[0], hud.HUD_MARGIN)
        self.assertAlmostEqual(
            trailing[2] - trailing[0],
            (background[2] - background[0]) * 0.8,
        )
        self.assertAlmostEqual(
            current[2] - current[0],
            (background[2] - background[0]) * 0.6,
        )
        self.assertGreater(trailing[2], current[2])

    def test_hp_trailing_bar_uses_the_current_hp_without_an_animation_tracker(self):
        gun = make_gun()

        _, rectangles = self._draw_hud(gun)

        trailing = rectangles[1]
        current = rectangles[2]
        self.assertEqual(trailing, current)

    def test_temperature_text_is_right_aligned_in_the_bottom_right(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "TEMP 10/200")
        self.assertEqual(text, "TEMP 10/200")
        self.assertEqual(x, SCREEN_WIDTH - hud.HUD_MARGIN - self.TEXT_WIDTH)
        self.assertEqual(y, hud.HUD_ROW_LOW)
        self.assertGreater(x, SCREEN_WIDTH / 2)
        self.assertLess(y, SCREEN_HEIGHT / 2)
        self.assertGreaterEqual(
            y - hud.HUD_FONT_SIZE / 2,
            hud.HUD_MARGIN + hud.TEMPERATURE_BAR_HEIGHT,
        )

    def test_hp_text_is_above_the_hp_bar(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "HP 100/100")
        self.assertGreaterEqual(
            y - hud.HUD_FONT_SIZE / 2,
            hud.HUD_MARGIN + hud.HP_BAR_HEIGHT,
        )

    def test_coin_text_is_above_the_hp_text(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        _, hp_y, _ = self._text_draw(font, "HP 100/100")
        _, coin_y, _ = self._text_draw(font, "COINS 7")
        self.assertGreaterEqual(
            coin_y - hud.HUD_FONT_SIZE / 2,
            hp_y + hud.HUD_FONT_SIZE / 2,
        )

    def test_damage_reduction_is_shown_in_the_bottom_right(self):
        gun = make_gun(damage_reduction=0.8)

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "DMG -80%")
        self.assertEqual(x, SCREEN_WIDTH - hud.HUD_MARGIN - self.TEXT_WIDTH)
        self.assertEqual(y, hud.HUD_ROW_HIGH)
        self.assertGreater(x, SCREEN_WIDTH / 2)
        self.assertLess(y, SCREEN_HEIGHT / 2)
        self.assertEqual(
            self._text_color(font, "DMG -80%"),
            hud.DAMAGE_REDUCTION_COLOR,
        )

    def test_damage_reduction_is_not_shown_when_fully_recovered(self):
        gun = make_gun(damage_reduction=0.0)

        font, _ = self._draw_hud(gun)

        self.assertFalse(
            any("DMG" in draw_call[2] for draw_call in font.draws)
        )

    def test_damage_reduction_time_is_shown_to_the_left_of_the_reduction(self):
        gun = make_gun(
            damage_reduction=0.8,
            damage_reduction_remaining=90.0,
        )

        font, _ = self._draw_hud(gun)

        reduction_x, reduction_y, _ = self._text_draw(font, "DMG -80%")
        time_x, time_y, _ = self._text_draw(font, "01:30")
        self.assertEqual(time_y, hud.HUD_ROW_HIGH)
        self.assertEqual(time_y, reduction_y)
        self.assertEqual(
            time_x,
            reduction_x - hud.DAMAGE_REDUCTION_TIME_GAP - self.TEXT_WIDTH,
        )
        self.assertEqual(
            self._text_color(font, "01:30"),
            hud.DAMAGE_REDUCTION_COLOR,
        )

    def test_damage_reduction_time_is_not_shown_without_a_reduction(self):
        gun = make_gun(
            damage_reduction=0.0,
            damage_reduction_remaining=30.0,
        )

        font, _ = self._draw_hud(gun)

        self.assertFalse(
            any(draw_call[2] == "00:30" for draw_call in font.draws)
        )

    def test_ready_status_is_not_drawn(self):
        gun = make_gun(can_fire=True)

        font, _ = self._draw_hud(gun)

        self.assertFalse(
            any(draw_call[2] == "READY" for draw_call in font.draws)
        )

    def test_temperature_warning_is_centered_on_the_gauge_at_160(self):
        gun = make_gun(temperature=160.0)

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "WARNING!")
        bar_left = SCREEN_WIDTH - hud.HUD_MARGIN - hud.TEMPERATURE_BAR_WIDTH
        self.assertEqual(
            x,
            bar_left + (hud.TEMPERATURE_BAR_WIDTH - self.TEXT_WIDTH) / 2,
        )
        self.assertEqual(
            y,
            hud.HUD_MARGIN + hud.TEMPERATURE_BAR_HEIGHT / 2,
        )
        self.assertEqual(
            self._text_color(font, "WARNING!"),
            hud.TEMPERATURE_WARNING_YELLOW_COLOR,
        )

    def test_temperature_warning_is_yellow_below_180(self):
        gun = make_gun(temperature=179.9)

        font, _ = self._draw_hud(gun)

        self.assertEqual(
            self._text_color(font, "WARNING!"),
            hud.TEMPERATURE_WARNING_YELLOW_COLOR,
        )

    def test_temperature_warning_is_red_from_180(self):
        gun = make_gun(temperature=180.0)

        font, _ = self._draw_hud(gun)

        self.assertEqual(
            self._text_color(font, "WARNING!"),
            hud.TEMPERATURE_WARNING_RED_COLOR,
        )

    def test_temperature_warning_is_red_at_199(self):
        gun = make_gun(temperature=199.0)

        font, _ = self._draw_hud(gun)

        self.assertEqual(
            self._text_color(font, "WARNING!"),
            hud.TEMPERATURE_WARNING_RED_COLOR,
        )

    def test_temperature_warning_is_hidden_below_160(self):
        gun = make_gun(temperature=159.9)

        font, _ = self._draw_hud(gun)

        self.assertFalse(
            any(draw_call[2] == "WARNING!" for draw_call in font.draws)
        )

    def test_temperature_warning_is_hidden_at_the_limit(self):
        gun = make_gun(temperature=200.0)

        font, _ = self._draw_hud(gun)

        self.assertFalse(
            any(draw_call[2] == "WARNING!" for draw_call in font.draws)
        )

    def test_overheat_status_is_centered_on_the_gauge(self):
        gun = make_gun(
            temperature=200.0,
            fire_blocked=True,
            can_fire=False,
        )

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "OVERHEAT")
        bar_left = SCREEN_WIDTH - hud.HUD_MARGIN - hud.TEMPERATURE_BAR_WIDTH
        self.assertEqual(
            x,
            bar_left + (hud.TEMPERATURE_BAR_WIDTH - self.TEXT_WIDTH) / 2,
        )
        self.assertEqual(
            y,
            hud.HUD_MARGIN + hud.TEMPERATURE_BAR_HEIGHT / 2,
        )

    def test_overheat_hides_the_temperature_warning(self):
        gun = make_gun(
            temperature=190.0,
            fire_blocked=True,
            can_fire=False,
        )

        font, _ = self._draw_hud(gun)

        self._text_draw(font, "OVERHEAT")
        self.assertFalse(
            any(draw_call[2] == "WARNING!" for draw_call in font.draws)
        )

    def test_wave_text_stays_at_the_top_of_the_screen(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "WAVE 1/30")
        self.assertEqual(y, SCREEN_HEIGHT - 25)
        self.assertGreater(y, SCREEN_HEIGHT / 2)

    def test_remaining_enemies_are_centered_below_the_wave_text(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "ENEMIES LEFT 12")
        self.assertEqual(x, (SCREEN_WIDTH - self.TEXT_WIDTH) / 2)
        self.assertEqual(y, hud.HUD_REMAINING_ENEMIES_Y)
        self.assertLess(y, SCREEN_HEIGHT - 25)
        self.assertGreater(y, SCREEN_HEIGHT / 2)


if __name__ == "__main__":
    unittest.main()
