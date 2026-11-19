import unittest

from shop import (
    DEFAULT_GUN_ID,
    MAX_UPGRADE_LEVEL,
    UPGRADE_COSTS,
    gun_price,
    upgrade_cost,
)


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


if __name__ == "__main__":
    unittest.main()
