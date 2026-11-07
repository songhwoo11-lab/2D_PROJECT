import unittest

from weapon import Gun, PISTOL


class GunTests(unittest.TestCase):
    def test_pistol_matches_prd_stats(self):
        self.assertEqual(PISTOL.damage, 5)
        self.assertEqual(PISTOL.fire_interval_frames, 10)
        self.assertAlmostEqual(PISTOL.fire_interval_seconds, 10 / 60)
        self.assertEqual(PISTOL.reload_seconds, 2.0)
        self.assertEqual(PISTOL.temperature_limit, 200.0)
        self.assertEqual(PISTOL.magazine_size, 10)
        self.assertEqual(PISTOL.starting_ammo, 100)

    def test_starting_ammunition_is_loaded_and_reserved(self):
        gun = Gun()

        self.assertEqual(gun.magazine_ammo, 10)
        self.assertEqual(gun.reserve_ammo, 90)
        self.assertEqual(gun.total_ammo, 100)

    def test_partial_starting_ammunition_fills_only_available_rounds(self):
        from weapon import WeaponSpec

        spec = WeaponSpec("Test", 1, 1, 1.0, 10.0, 10, 4)
        gun = Gun(spec)

        self.assertEqual((gun.magazine_ammo, gun.reserve_ammo), (4, 0))

    def test_single_shot_consumes_ammo_and_obeys_ten_frame_interval(self):
        gun = Gun()

        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.magazine_ammo, 9)
        self.assertFalse(gun.try_fire())

        gun.update(9 / 60)
        self.assertFalse(gun.try_fire())
        gun.update(1 / 60)
        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.magazine_ammo, 8)

    def test_firing_rejects_invalid_delta_time(self):
        with self.assertRaisesRegex(ValueError, "delta_time"):
            Gun().update(-0.1)


if __name__ == "__main__":
    unittest.main()
