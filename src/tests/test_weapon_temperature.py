import unittest

from game_config import MIN_TEMPERATURE, PISTOL_TEMPERATURE_LIMIT
from weapon import Gun


class GunTemperatureStateTests(unittest.TestCase):
    def test_new_gun_starts_at_minimum_temperature_and_can_fire(self):
        gun = Gun()

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertEqual(gun.temperature_limit, PISTOL_TEMPERATURE_LIMIT)
        self.assertFalse(gun.fire_blocked)
        self.assertTrue(gun.can_fire)

    def test_overheated_gun_is_blocked_from_firing(self):
        gun = Gun()
        gun.overheated = True

        self.assertTrue(gun.fire_blocked)
        self.assertFalse(gun.can_fire)

    def test_reset_restores_temperature_and_clears_overheat(self):
        gun = Gun()
        gun.temperature = 123.0
        gun.overheated = True

        gun.reset()

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertFalse(gun.fire_blocked)
        self.assertTrue(gun.can_fire)


if __name__ == "__main__":
    unittest.main()
