import unittest

from weapon import Gun


class MagazineRefillTests(unittest.TestCase):
    def test_refill_adds_the_requested_amount(self):
        gun = Gun()
        gun.magazine_ammo = 3

        added = gun.refill_magazine(5)

        self.assertEqual(added, 5)
        self.assertEqual(gun.magazine_ammo, 8)

    def test_refill_never_exceeds_magazine_capacity(self):
        gun = Gun()
        gun.magazine_ammo = 8

        added = gun.refill_magazine(5)

        self.assertEqual(added, 2)
        self.assertEqual(gun.magazine_ammo, gun.spec.magazine_size)

    def test_full_magazine_accepts_no_ammunition(self):
        gun = Gun()

        added = gun.refill_magazine(5)

        self.assertEqual(added, 0)
        self.assertEqual(gun.magazine_ammo, gun.spec.magazine_size)

    def test_negative_refill_is_rejected(self):
        gun = Gun()

        with self.assertRaises(ValueError):
            gun.refill_magazine(-1)


if __name__ == "__main__":
    unittest.main()
