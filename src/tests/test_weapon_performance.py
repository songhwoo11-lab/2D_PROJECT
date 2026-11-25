import unittest

from game_config import (
    FPS,
    MACHINE_GUN_FIRE_INTERVAL_SECONDS,
    PISTOL_FIRE_INTERVAL_SECONDS,
    RIFLE_FIRE_INTERVAL_SECONDS,
)
from weapon import (
    DEFAULT_GUN_ID,
    MACHINE_GUN_GUN_ID,
    RIFLE_GUN_ID,
    Gun,
)


EXPECTED_STATS = {
    DEFAULT_GUN_ID: {
        "damage": 5,
        "fire_interval_seconds": PISTOL_FIRE_INTERVAL_SECONDS,
        "fire_interval_frames": PISTOL_FIRE_INTERVAL_SECONDS * FPS,
        "reload_seconds": 3.0,
        "temperature_limit": 200.0,
        "magazine_size": 10,
        "starting_ammo": 100,
    },
    RIFLE_GUN_ID: {
        "damage": 20,
        "fire_interval_seconds": RIFLE_FIRE_INTERVAL_SECONDS,
        "fire_interval_frames": RIFLE_FIRE_INTERVAL_SECONDS * FPS,
        "reload_seconds": 4.0,
        "temperature_limit": 300.0,
        "magazine_size": 30,
        "starting_ammo": 300,
    },
    MACHINE_GUN_GUN_ID: {
        "damage": 12,
        "fire_interval_seconds": MACHINE_GUN_FIRE_INTERVAL_SECONDS,
        "fire_interval_frames": MACHINE_GUN_FIRE_INTERVAL_SECONDS * FPS,
        "reload_seconds": 5.0,
        "temperature_limit": 500.0,
        "magazine_size": 50,
        "starting_ammo": 500,
    },
}


class WeaponPerformanceTests(unittest.TestCase):
    def test_prd_stats_are_applied_to_each_gun(self):
        for gun_id, expected in EXPECTED_STATS.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)

                self.assertEqual(gun.effective_damage, expected["damage"])
                self.assertAlmostEqual(
                    gun.fire_interval_seconds,
                    expected["fire_interval_seconds"],
                )
                self.assertAlmostEqual(
                    gun.fire_interval_frames,
                    expected["fire_interval_frames"],
                )
                self.assertEqual(gun.reload_seconds, expected["reload_seconds"])
                self.assertEqual(
                    gun.temperature_limit,
                    expected["temperature_limit"],
                )
                self.assertEqual(gun.magazine_size, expected["magazine_size"])
                self.assertEqual(gun.starting_ammo, expected["starting_ammo"])
                self.assertEqual(gun.total_ammo, expected["starting_ammo"])

    def test_each_gun_fires_at_its_own_interval(self):
        for gun_id, expected in EXPECTED_STATS.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)
                gun.toggle_mode()

                self.assertTrue(gun.try_fire())
                self.assertAlmostEqual(
                    gun.cooldown_remaining,
                    expected["fire_interval_seconds"],
                )

    def test_each_gun_reloads_for_its_own_duration(self):
        for gun_id, expected in EXPECTED_STATS.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)
                gun.magazine_ammo = 0

                self.assertTrue(gun.start_reload())
                self.assertAlmostEqual(
                    gun.reload_remaining,
                    expected["reload_seconds"],
                )
                gun.update(expected["reload_seconds"])

                self.assertFalse(gun.reloading)
                self.assertEqual(gun.magazine_ammo, expected["magazine_size"])

    def test_each_gun_overheats_at_its_own_limit(self):
        for gun_id, expected in EXPECTED_STATS.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)
                gun._add_heat(expected["temperature_limit"] + 50)

                self.assertEqual(gun.temperature, expected["temperature_limit"])
                self.assertTrue(gun.overheated)
                self.assertFalse(gun.can_fire)


if __name__ == "__main__":
    unittest.main()
