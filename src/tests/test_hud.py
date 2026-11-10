import unittest
from types import SimpleNamespace

from hud import coin_text, fire_status_text, temperature_text, wave_text


def make_gun(**overrides):
    values = {
        "temperature": 10.0,
        "temperature_limit": 200.0,
        "fire_blocked": False,
        "can_fire": True,
        "reloading": False,
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


if __name__ == "__main__":
    unittest.main()
