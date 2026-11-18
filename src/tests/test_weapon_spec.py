import unittest
from dataclasses import FrozenInstanceError

from game_config import (
    PISTOL_DAMAGE,
    PISTOL_FIRE_INTERVAL_SECONDS,
    PISTOL_MAGAZINE_SIZE,
    PISTOL_RELOAD_SECONDS,
    PISTOL_STARTING_AMMO,
    PISTOL_TEMPERATURE_LIMIT,
)
from weapon import (
    DEFAULT_GUN_ID,
    PISTOL,
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
