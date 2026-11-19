import unittest

from game_state import GameState
from shop import (
    DEFAULT_GUN_ID,
    MAX_UPGRADE_LEVEL,
    UPGRADE_COSTS,
    UPGRADE_PROBABILITIES,
    UpgradeResult,
    gun_price,
    upgrade_chances,
    upgrade_cost,
    upgrade_gun,
)
from weapon import UPGRADE_EFFECTS, weapon_stats_at_level


class UpgradeCostTests(unittest.TestCase):
    def test_upgrade_costs_follow_the_prd(self):
        self.assertEqual(
            UPGRADE_COSTS[DEFAULT_GUN_ID],
            (10, 100, 200, 400, 800, 1000, 2000, 4000, 8000, 10000),
        )
        self.assertEqual(
            UPGRADE_COSTS["rifle"],
            (100, 500, 1000, 2000, 4000, 8000, 10000, 15000, 20000, 40000),
        )
        self.assertEqual(
            UPGRADE_COSTS["machine_gun"],
            (1000, 5000, 10000, 20000, 30000, 50000, 60000, 70000, 80000, 100000),
        )

    def test_upgrade_cost_uses_the_current_level(self):
        self.assertEqual(upgrade_cost("pistol", 0), 10)
        self.assertEqual(upgrade_cost("rifle", 4), 4000)
        self.assertEqual(upgrade_cost("machine_gun", 9), 100000)

    def test_upgrade_cost_rejects_invalid_levels(self):
        with self.assertRaises(IndexError):
            upgrade_cost("pistol", -1)
        with self.assertRaises(IndexError):
            upgrade_cost("pistol", MAX_UPGRADE_LEVEL)

    def test_upgrade_cost_rejects_unknown_gun(self):
        with self.assertRaises(KeyError):
            upgrade_cost("unknown", 0)


class UpgradeProbabilityTests(unittest.TestCase):
    def test_probabilities_follow_the_prd(self):
        self.assertEqual(
            UPGRADE_PROBABILITIES,
            (
                (100, 0, 0, 0),
                (90, 9, 1, 0),
                (80, 18, 2, 0),
                (70, 27, 3, 0),
                (60, 36, 4, 0),
                (50, 44, 5, 1),
                (40, 52, 6, 2),
                (30, 60, 7, 3),
                (20, 68, 8, 4),
                (10, 76, 9, 5),
            ),
        )

    def test_each_level_totals_one_hundred_percent(self):
        for chances in UPGRADE_PROBABILITIES:
            self.assertEqual(sum(chances), 100)

    def test_chances_are_returned_by_level(self):
        first = upgrade_chances(0)
        self.assertEqual(
            (first.success, first.failure, first.downgrade, first.destroy),
            (100, 0, 0, 0),
        )
        last = upgrade_chances(9)
        self.assertEqual(
            (last.success, last.failure, last.downgrade, last.destroy),
            (10, 76, 9, 5),
        )
        with self.assertRaises(IndexError):
            upgrade_chances(MAX_UPGRADE_LEVEL)


class UpgradeEffectDataTests(unittest.TestCase):
    def test_effects_cover_every_level(self):
        for gun_id, effects in UPGRADE_EFFECTS.items():
            self.assertEqual(len(effects.damage), MAX_UPGRADE_LEVEL + 1)
            self.assertEqual(len(effects.magazine_size), MAX_UPGRADE_LEVEL + 1)
            self.assertEqual(len(effects.reload_seconds), MAX_UPGRADE_LEVEL + 1)

    def test_effects_apply_at_the_target_level(self):
        base = weapon_stats_at_level("rifle", 0)
        upgraded = weapon_stats_at_level("rifle", 1)

        self.assertEqual(upgraded.damage, 25)
        self.assertEqual(upgraded.magazine_size, 30)
        self.assertEqual(upgraded.reload_seconds, 3.0)
        self.assertEqual(upgraded.fire_interval_seconds, base.fire_interval_seconds)


class UpgradeEngineTests(unittest.TestCase):
    def test_level_zero_upgrade_is_guaranteed(self):
        state = GameState(owned_guns=["pistol"], coins=100)

        outcome = upgrade_gun(state, "pistol", roll=100)

        self.assertEqual(outcome.result, UpgradeResult.SUCCESS)
        self.assertEqual(outcome.level_before, 0)
        self.assertEqual(outcome.level_after, 1)
        self.assertEqual(state.upgrade_level("pistol"), 1)

    def test_upgrade_levels_start_at_zero_for_every_gun(self):
        state = GameState()

        self.assertEqual(state.upgrade_level("pistol"), 0)
        self.assertEqual(state.upgrade_level("rifle"), 0)
        self.assertEqual(state.upgrade_level("machine_gun"), 0)


if __name__ == "__main__":
    unittest.main()
