import unittest

from weapon import DEFAULT_GUN_ID, MACHINE_GUN_GUN_ID, RIFLE_GUN_ID, WeaponStates


class WeaponStatesAmmoTests(unittest.TestCase):
    def setUp(self):
        self.states = WeaponStates()

    def test_each_gun_starts_with_its_own_ammo(self):
        snapshots = self.states.ammo_snapshot

        self.assertEqual(
            snapshots[DEFAULT_GUN_ID],
            (10, 90),
        )
        self.assertEqual(
            snapshots[RIFLE_GUN_ID],
            (30, 270),
        )
        self.assertEqual(
            snapshots[MACHINE_GUN_GUN_ID],
            (50, 450),
        )

    def test_switching_guns_keeps_ammo_separate(self):
        self.states.gun.try_fire()
        self.states.gun.try_fire()
        pistol_ammo = (self.states.gun.magazine_ammo, self.states.gun.reserve_ammo)

        self.states.select(RIFLE_GUN_ID)
        self.assertEqual(self.states.current_id, RIFLE_GUN_ID)
        self.assertEqual(self.states.gun.magazine_ammo, 30)

        self.states.gun.try_fire()
        rifle_ammo = (self.states.gun.magazine_ammo, self.states.gun.reserve_ammo)

        self.states.select(DEFAULT_GUN_ID)

        self.assertEqual(
            (self.states.gun.magazine_ammo, self.states.gun.reserve_ammo),
            pistol_ammo,
        )
        self.assertEqual(self.states.ammo_snapshot[RIFLE_GUN_ID], rifle_ammo)

    def test_reserve_pickups_only_change_the_selected_gun(self):
        self.states.gun.add_reserve_ammo(10)

        self.assertEqual(self.states.ammo_snapshot[DEFAULT_GUN_ID][1], 100)
        self.assertEqual(self.states.ammo_snapshot[RIFLE_GUN_ID][1], 270)

    def test_unmanaged_guns_are_rejected(self):
        states = WeaponStates(gun_ids=[DEFAULT_GUN_ID])

        with self.assertRaises(ValueError):
            states.select(RIFLE_GUN_ID)

    def test_initial_gun_must_be_managed(self):
        with self.assertRaises(ValueError):
            WeaponStates(
                gun_ids=[DEFAULT_GUN_ID],
                initial_gun_id=MACHINE_GUN_GUN_ID,
            )


class WeaponStatesThermalAndReloadTests(unittest.TestCase):
    def setUp(self):
        self.states = WeaponStates()

    def test_temperature_is_separate_for_each_gun(self):
        self.states.gun.temperature = 120.0
        self.states.select(RIFLE_GUN_ID)
        self.states.gun.temperature = 210.0

        self.states.select(DEFAULT_GUN_ID)

        self.assertEqual(self.states.gun.temperature, 120.0)
        self.states.select(RIFLE_GUN_ID)
        self.assertEqual(self.states.gun.temperature, 210.0)

    def test_reload_state_is_separate_for_each_gun(self):
        self.states.gun.reload_remaining = 1.5
        self.states.select(RIFLE_GUN_ID)
        self.states.gun.reload_remaining = 0.5

        self.states.select(DEFAULT_GUN_ID)

        self.assertTrue(self.states.gun.reloading)
        self.assertEqual(self.states.gun.reload_remaining, 1.5)
        self.states.select(RIFLE_GUN_ID)
        self.assertEqual(self.states.gun.reload_remaining, 0.5)

    def test_heat_settings_are_separate_for_each_gun(self):
        self.states.gun.heat_enabled = False
        self.states.gun.infinite_ammo = True
        self.states.select(RIFLE_GUN_ID)

        self.assertTrue(self.states.gun.heat_enabled)
        self.assertFalse(self.states.gun.infinite_ammo)

        self.states.select(DEFAULT_GUN_ID)

        self.assertFalse(self.states.gun.heat_enabled)
        self.assertTrue(self.states.gun.infinite_ammo)

    def test_state_snapshot_contains_temperature_and_reload(self):
        snapshot = self.states.state_snapshot

        self.assertIn("temperature", snapshot[DEFAULT_GUN_ID])
        self.assertIn("reload_remaining", snapshot[RIFLE_GUN_ID])


if __name__ == "__main__":
    unittest.main()
