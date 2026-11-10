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


class SingleShotHeatTests(unittest.TestCase):
    def _ready_gun(self):
        gun = Gun()
        gun.infinite_ammo = True
        return gun

    def test_each_single_shot_adds_half_a_degree(self):
        gun = self._ready_gun()

        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)
        gun.cooldown_remaining = 0.0
        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.0)

    def test_blocked_shot_does_not_add_heat(self):
        gun = self._ready_gun()
        gun.overheated = True
        gun.temperature = 42.0

        self.assertFalse(gun.try_fire())
        self.assertEqual(gun.temperature, 42.0)

    def test_temperature_is_clamped_to_limit(self):
        gun = self._ready_gun()
        gun.temperature = gun.temperature_limit - 0.2

        gun.try_fire()

        self.assertEqual(gun.temperature, gun.temperature_limit)


if __name__ == "__main__":
    unittest.main()
