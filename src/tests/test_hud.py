import unittest
from types import SimpleNamespace
from unittest import mock

import hud
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from hud import (
    coin_text,
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

    def test_ready_is_shown_when_gun_can_fire(self):
        gun = make_gun(can_fire=True)

        self.assertEqual(fire_status_text(gun), "READY")

    def test_no_status_is_shown_during_fire_cooldown(self):
        gun = make_gun(can_fire=False, reloading=False)

        self.assertIsNone(fire_status_text(gun))

    def test_reloading_is_not_reported_as_ready_or_overheat(self):
        gun = make_gun(can_fire=False, reloading=True)

        self.assertIsNone(fire_status_text(gun))


class RecordingFont:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, text, color=(255, 255, 255)):
        self.draws.append((x, y, text))


class HudLayoutTests(unittest.TestCase):
    TEXT_WIDTH = 60

    def _draw_hud(self, gun):
        font = RecordingFont()
        rectangles = []

        def draw_rectangle(x1, y1, x2, y2, r, g, b, a, filled):
            rectangles.append((x1, y1, x2, y2))

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
                return draw_call
        self.fail("text {!r} was not drawn".format(text))

    def test_temperature_bar_is_in_the_bottom_right_corner(self):
        gun = make_gun()

        _, rectangles = self._draw_hud(gun)

        bar = rectangles[2]
        self.assertEqual(
            bar,
            (
                SCREEN_WIDTH - hud.HUD_MARGIN - hud.TEMPERATURE_BAR_WIDTH,
                hud.HUD_MARGIN,
                SCREEN_WIDTH - hud.HUD_MARGIN,
                hud.HUD_MARGIN + hud.TEMPERATURE_BAR_HEIGHT,
            ),
        )

    def test_temperature_text_is_right_aligned_in_the_bottom_right(self):
        gun = make_gun()

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "TEMP 10/200")
        self.assertEqual(text, "TEMP 10/200")
        self.assertEqual(x, SCREEN_WIDTH - hud.HUD_MARGIN - self.TEXT_WIDTH)
        self.assertEqual(y, hud.HUD_ROW_LOW)
        self.assertGreater(x, SCREEN_WIDTH / 2)
        self.assertLess(y, SCREEN_HEIGHT / 2)

    def test_ready_status_is_in_the_bottom_right(self):
        gun = make_gun(can_fire=True)

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "READY")
        self.assertEqual(x, SCREEN_WIDTH - hud.HUD_MARGIN - self.TEXT_WIDTH)
        self.assertEqual(y, hud.HUD_ROW_HIGH)
        self.assertGreater(x, SCREEN_WIDTH / 2)
        self.assertLess(y, SCREEN_HEIGHT / 2)

    def test_overheat_status_is_in_the_bottom_right(self):
        gun = make_gun(fire_blocked=True, can_fire=False)

        font, _ = self._draw_hud(gun)

        x, y, text = self._text_draw(font, "OVERHEAT")
        self.assertEqual(x, SCREEN_WIDTH - hud.HUD_MARGIN - self.TEXT_WIDTH)
        self.assertEqual(y, hud.HUD_ROW_HIGH)
        self.assertGreater(x, SCREEN_WIDTH / 2)
        self.assertLess(y, SCREEN_HEIGHT / 2)

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
