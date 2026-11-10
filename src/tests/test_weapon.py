import unittest

from weapon import FireMode, Gun, PISTOL


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

    def test_single_shot_consumes_ammo_and_uses_half_auto_fire_rate(self):
        gun = Gun()

        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.magazine_ammo, 9)
        self.assertFalse(gun.try_fire())

        gun.update(19 / 60)
        self.assertFalse(gun.try_fire())
        gun.update(1 / 60)
        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.magazine_ammo, 8)

    def test_single_shot_uses_twice_auto_interval_for_custom_weapon(self):
        from weapon import WeaponSpec

        gun = Gun(WeaponSpec("Fast", 1, 1, 1.0, 10.0, 10, 10))

        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.cooldown_remaining, 2 / 60)

    def test_auto_mode_keeps_configured_fire_interval(self):
        gun = Gun()
        gun.toggle_mode()

        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.cooldown_remaining, 10 / 60)

    def test_firing_rejects_invalid_delta_time(self):
        with self.assertRaisesRegex(ValueError, "delta_time"):
            Gun().update(-0.1)

    def test_fire_mode_toggles_between_single_and_auto(self):
        gun = Gun()

        self.assertIs(gun.fire_mode, FireMode.SINGLE)
        self.assertIs(gun.toggle_mode(), FireMode.AUTO)
        self.assertIs(gun.toggle_mode(), FireMode.SINGLE)

    def test_toggling_mode_preserves_ammunition_and_cooldown(self):
        gun = Gun()
        gun.try_fire()
        ammo = gun.magazine_ammo
        cooldown = gun.cooldown_remaining

        gun.toggle_mode()

        self.assertEqual(gun.magazine_ammo, ammo)
        self.assertEqual(gun.cooldown_remaining, cooldown)

    def test_single_mode_uses_click_edge_not_held_state(self):
        gun = Gun()

        self.assertFalse(gun.handle_fire_input(mouse_held=True))
        self.assertTrue(gun.handle_fire_input(mouse_held=True, mouse_pressed=True))
        self.assertFalse(gun.handle_fire_input(mouse_held=True))
        self.assertEqual(gun.magazine_ammo, 9)

    def test_auto_mode_fires_while_held_at_configured_interval(self):
        gun = Gun()
        gun.toggle_mode()

        self.assertTrue(gun.handle_fire_input(mouse_held=True))
        self.assertFalse(gun.handle_fire_input(mouse_held=True))
        gun.update(10 / 60)
        self.assertTrue(gun.handle_fire_input(mouse_held=True))
        self.assertEqual(gun.magazine_ammo, 8)

    def test_auto_mode_does_not_fire_when_released(self):
        gun = Gun()
        gun.toggle_mode()

        self.assertFalse(gun.handle_fire_input(mouse_held=False))
        self.assertEqual(gun.magazine_ammo, 10)

    def test_empty_magazine_blocks_single_and_auto_fire(self):
        gun = Gun()
        gun.magazine_ammo = 0
        gun.toggle_mode()

        self.assertFalse(gun.can_fire)
        self.assertFalse(gun.handle_fire_input(mouse_held=True))
        self.assertFalse(gun.handle_fire_input(mouse_held=True, mouse_pressed=True))
        self.assertEqual(gun.magazine_ammo, 0)
        self.assertEqual(gun.reserve_ammo, 90)

    def test_manual_reload_transfers_reserve_after_prd_duration(self):
        gun = Gun()
        gun.magazine_ammo = 0

        self.assertTrue(gun.start_reload())
        self.assertTrue(gun.reloading)
        self.assertFalse(gun.try_fire())
        gun.update(119 / 60)
        self.assertEqual(gun.magazine_ammo, 0)
        gun.update(1 / 60)

        self.assertFalse(gun.reloading)
        self.assertEqual(gun.magazine_ammo, 10)
        self.assertEqual(gun.reserve_ammo, 80)

    def test_empty_click_starts_automatic_reload(self):
        gun = Gun()
        gun.magazine_ammo = 0

        self.assertFalse(gun.handle_fire_input(mouse_held=True, mouse_pressed=True))
        self.assertTrue(gun.reloading)
        self.assertEqual(gun.reserve_ammo, 90)

    def test_infinite_ammo_allows_firing_without_changing_ammo_or_reloading(self):
        gun = Gun()
        gun.magazine_ammo = 0
        gun.reserve_ammo = 17
        gun.infinite_ammo = True

        self.assertTrue(gun.can_fire)
        self.assertTrue(gun.handle_fire_input(mouse_held=True, mouse_pressed=True))
        self.assertEqual((gun.magazine_ammo, gun.reserve_ammo), (0, 17))
        self.assertFalse(gun.start_reload())
        self.assertFalse(gun.reloading)

    def test_reload_does_not_overfill_or_start_without_reserve(self):
        gun = Gun()
        gun.magazine_ammo = 9
        gun.reserve_ammo = 1
        self.assertTrue(gun.start_reload())
        gun.update(gun.spec.reload_seconds)
        self.assertEqual((gun.magazine_ammo, gun.reserve_ammo), (10, 0))
        self.assertFalse(gun.start_reload())


if __name__ == "__main__":
    unittest.main()
