import unittest

from weapon import Gun


class ReserveAmmoTests(unittest.TestCase):
    def test_reserve_ammo_gains_the_requested_amount(self):
        gun = Gun()
        gun.reserve_ammo = 20

        added = gun.add_reserve_ammo(10)

        self.assertEqual(added, 10)
        self.assertEqual(gun.reserve_ammo, 30)

    def test_reserve_ammo_growth_is_not_limited_by_magazine_capacity(self):
        gun = Gun()
        gun.magazine_ammo = gun.spec.magazine_size

        added = gun.add_reserve_ammo(10)

        self.assertEqual(added, 10)
        self.assertEqual(gun.reserve_ammo, 100)
        self.assertEqual(gun.magazine_ammo, gun.spec.magazine_size)

    def test_loaded_magazine_is_untouched(self):
        gun = Gun()
        gun.magazine_ammo = 3

        gun.add_reserve_ammo(10)

        self.assertEqual(gun.magazine_ammo, 3)

    def test_negative_reserve_amount_is_rejected(self):
        gun = Gun()

        with self.assertRaises(ValueError):
            gun.add_reserve_ammo(-1)


if __name__ == "__main__":
    unittest.main()
