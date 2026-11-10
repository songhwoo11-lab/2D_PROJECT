import unittest

from player import Player


class PlayerHealTests(unittest.TestCase):
    def test_heal_restores_hp(self):
        player = Player(0, 0)
        player.hp = 50

        healed = player.heal(10)

        self.assertEqual(healed, 10)
        self.assertEqual(player.hp, 60)

    def test_heal_does_not_exceed_max_hp(self):
        player = Player(0, 0)
        player.hp = 95

        healed = player.heal(10)

        self.assertEqual(healed, 5)
        self.assertEqual(player.hp, player.max_hp)

    def test_full_hp_accepts_no_healing(self):
        player = Player(0, 0)

        healed = player.heal(10)

        self.assertEqual(healed, 0)
        self.assertEqual(player.hp, player.max_hp)

    def test_negative_heal_is_rejected(self):
        player = Player(0, 0)

        with self.assertRaises(ValueError):
            player.heal(-1)


if __name__ == "__main__":
    unittest.main()
