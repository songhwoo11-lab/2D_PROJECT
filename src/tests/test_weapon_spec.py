import unittest
from dataclasses import FrozenInstanceError

from game_config import (
    FPS,
    MACHINE_GUN_DAMAGE,
    MACHINE_GUN_FIRE_INTERVAL_SECONDS,
    MACHINE_GUN_MAGAZINE_SIZE,
    MACHINE_GUN_RELOAD_SECONDS,
    MACHINE_GUN_STARTING_AMMO,
    MACHINE_GUN_TEMPERATURE_LIMIT,
    PISTOL_DAMAGE,
    PISTOL_FIRE_INTERVAL_SECONDS,
    PISTOL_MAGAZINE_SIZE,
    PISTOL_RELOAD_SECONDS,
    PISTOL_STARTING_AMMO,
    PISTOL_TEMPERATURE_LIMIT,
    RIFLE_DAMAGE,
    RIFLE_FIRE_INTERVAL_SECONDS,
    RIFLE_MAGAZINE_SIZE,
    RIFLE_RELOAD_SECONDS,
    RIFLE_STARTING_AMMO,
    RIFLE_TEMPERATURE_LIMIT,
    SINGLE_FIRE_INTERVAL_MULTIPLIER,
)
from weapon import (
    DEFAULT_GUN_ID,
    PISTOL,
    Gun,
    MACHINE_GUN,
    MACHINE_GUN_GUN_ID,
    RIFLE,
    RIFLE_GUN_ID,
    WeaponSpec,
    weapon_display_name,
    weapon_spec,
    weapon_spec_or_default,
)


class WeaponSpecModelTests(unittest.TestCase):
    def test_weapon_spec_holds_all_shared_stats(self):
        self.assertEqual(PISTOL.name, "Pistol")
        self.assertEqual(PISTOL.damage, PISTOL_DAMAGE)
        self.assertEqual(PISTOL.fire_interval_seconds, PISTOL_FIRE_INTERVAL_SECONDS)
        self.assertEqual(PISTOL.reload_seconds, PISTOL_RELOAD_SECONDS)
        self.assertEqual(PISTOL.temperature_limit, PISTOL_TEMPERATURE_LIMIT)
        self.assertEqual(PISTOL.magazine_size, PISTOL_MAGAZINE_SIZE)
        self.assertEqual(PISTOL.starting_ammo, PISTOL_STARTING_AMMO)

    def test_weapon_spec_is_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            PISTOL.damage = 999

    def test_registered_spec_lookup(self):
        self.assertIs(weapon_spec(DEFAULT_GUN_ID), PISTOL)
        self.assertIs(weapon_spec_or_default(DEFAULT_GUN_ID), PISTOL)
        self.assertEqual(weapon_display_name(DEFAULT_GUN_ID), "PISTOL")

    def test_unknown_id_falls_back_to_the_default_spec(self):
        self.assertIs(weapon_spec_or_default("unknown"), PISTOL)
        self.assertEqual(weapon_display_name("unknown"), "UNKNOWN")

    def test_unknown_registered_lookup_raises(self):
        with self.assertRaises(KeyError):
            weapon_spec("unknown")

    def test_rifle_uses_the_prd_stats(self):
        self.assertEqual(RIFLE.damage, RIFLE_DAMAGE)
        self.assertEqual(RIFLE.fire_interval_seconds, RIFLE_FIRE_INTERVAL_SECONDS)
        self.assertEqual(RIFLE.reload_seconds, RIFLE_RELOAD_SECONDS)
        self.assertEqual(RIFLE.temperature_limit, RIFLE_TEMPERATURE_LIMIT)
        self.assertEqual(RIFLE.magazine_size, RIFLE_MAGAZINE_SIZE)
        self.assertEqual(RIFLE.starting_ammo, RIFLE_STARTING_AMMO)
        self.assertIs(weapon_spec(RIFLE_GUN_ID), RIFLE)
        self.assertEqual(weapon_display_name(RIFLE_GUN_ID), "RIFLE")

    def test_machine_gun_uses_the_prd_stats(self):
        self.assertEqual(MACHINE_GUN.damage, MACHINE_GUN_DAMAGE)
        self.assertEqual(
            MACHINE_GUN.fire_interval_seconds,
            MACHINE_GUN_FIRE_INTERVAL_SECONDS,
        )
        self.assertEqual(MACHINE_GUN.reload_seconds, MACHINE_GUN_RELOAD_SECONDS)
        self.assertEqual(
            MACHINE_GUN.temperature_limit,
            MACHINE_GUN_TEMPERATURE_LIMIT,
        )
        self.assertEqual(MACHINE_GUN.magazine_size, MACHINE_GUN_MAGAZINE_SIZE)
        self.assertEqual(MACHINE_GUN.starting_ammo, MACHINE_GUN_STARTING_AMMO)
        self.assertIs(weapon_spec(MACHINE_GUN_GUN_ID), MACHINE_GUN)
        self.assertEqual(weapon_display_name(MACHINE_GUN_GUN_ID), "MACHINE GUN")

    def test_gun_connects_to_the_registered_pistol_spec(self):
        gun = Gun.from_gun_id(DEFAULT_GUN_ID)

        self.assertIs(gun.spec, PISTOL)
        self.assertEqual(gun.gun_id, DEFAULT_GUN_ID)
        self.assertEqual(gun.effective_damage, PISTOL_DAMAGE)

    def test_each_gun_applies_its_own_fire_interval(self):
        expected_frames = {
            DEFAULT_GUN_ID: 10,
            RIFLE_GUN_ID: 5,
            MACHINE_GUN_GUN_ID: 1,
        }
        for gun_id, frames in expected_frames.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)

                self.assertAlmostEqual(gun.fire_interval_frames, frames)
                self.assertTrue(gun.try_fire())
                self.assertAlmostEqual(
                    gun.cooldown_remaining,
                    gun.fire_interval_seconds * SINGLE_FIRE_INTERVAL_MULTIPLIER,
                )
                self.assertAlmostEqual(
                    gun.fire_interval_seconds * FPS,
                    gun.spec.fire_interval_seconds * FPS,
                )

    def test_each_gun_applies_its_own_magazine_and_starting_ammo(self):
        specs = {
            DEFAULT_GUN_ID: PISTOL,
            RIFLE_GUN_ID: RIFLE,
            MACHINE_GUN_GUN_ID: MACHINE_GUN,
        }
        for gun_id, spec in specs.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)

                self.assertEqual(gun.magazine_size, spec.magazine_size)
                self.assertEqual(gun.starting_ammo, spec.starting_ammo)
                self.assertEqual(gun.magazine_ammo, spec.magazine_size)
                self.assertEqual(
                    gun.reserve_ammo,
                    spec.starting_ammo - spec.magazine_size,
                )
                self.assertEqual(gun.total_ammo, spec.starting_ammo)

    def test_each_gun_applies_its_own_reload_time(self):
        for gun_id, spec in {
            DEFAULT_GUN_ID: PISTOL,
            RIFLE_GUN_ID: RIFLE,
            MACHINE_GUN_GUN_ID: MACHINE_GUN,
        }.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)
                gun.magazine_ammo = 0

                self.assertEqual(gun.reload_seconds, spec.reload_seconds)
                self.assertTrue(gun.start_reload())
                self.assertAlmostEqual(gun.reload_remaining, spec.reload_seconds)

    def test_each_gun_applies_its_own_temperature_limit(self):
        for gun_id, spec in {
            DEFAULT_GUN_ID: PISTOL,
            RIFLE_GUN_ID: RIFLE,
            MACHINE_GUN_GUN_ID: MACHINE_GUN,
        }.items():
            with self.subTest(gun_id=gun_id):
                gun = Gun.from_gun_id(gun_id)

                self.assertEqual(gun.temperature_limit, spec.temperature_limit)
                gun._add_heat(spec.temperature_limit + 100)

                self.assertEqual(gun.temperature, spec.temperature_limit)
                self.assertTrue(gun.overheated)
                self.assertTrue(gun.fire_blocked)

    def test_new_spec_can_be_created_from_the_common_model(self):
        spec = WeaponSpec(
            name="Test",
            damage=7,
            fire_interval_seconds=0.1,
            reload_seconds=1.0,
            temperature_limit=150.0,
            magazine_size=12,
            starting_ammo=60,
        )

        self.assertEqual(spec.damage, 7)
        self.assertEqual(spec.magazine_size, 12)


if __name__ == "__main__":
    unittest.main()
