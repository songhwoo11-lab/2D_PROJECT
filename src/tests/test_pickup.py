import random
import unittest

from pickup import (
    MagazinePickup,
    magazine_drop_chance,
    roll_coin_reward,
    roll_magazine_drop,
)


class StubRandom:
    def __init__(self, coin=1, roll=0.0):
        self.coin = coin
        self.roll = roll

    def randint(self, minimum, maximum):
        return self.coin

    def random(self):
        return self.roll


class PlayerStub:
    radius = 16.0

    def __init__(self, x, y):
        self.x = x
        self.y = y


class CoinRewardTests(unittest.TestCase):
    def test_coin_reward_is_between_one_and_five(self):
        rng = random.Random(0)

        rewards = [roll_coin_reward(rng) for _ in range(200)]

        self.assertGreaterEqual(min(rewards), 1)
        self.assertLessEqual(max(rewards), 5)
        self.assertEqual(set(rewards), {1, 2, 3, 4, 5})


class MagazineDropChanceTests(unittest.TestCase):
    def test_chances_follow_the_ammunition_tiers(self):
        self.assertEqual(magazine_drop_chance(0), 0.30)
        self.assertEqual(magazine_drop_chance(99), 0.30)
        self.assertEqual(magazine_drop_chance(100), 0.10)
        self.assertEqual(magazine_drop_chance(199), 0.10)
        self.assertEqual(magazine_drop_chance(200), 0.01)
        self.assertEqual(magazine_drop_chance(299), 0.01)
        self.assertEqual(magazine_drop_chance(300), 0.0)
        self.assertEqual(magazine_drop_chance(1000), 0.0)

    def test_drop_roll_uses_the_tier_chance(self):
        self.assertTrue(roll_magazine_drop(50, StubRandom(roll=0.29)))
        self.assertFalse(roll_magazine_drop(50, StubRandom(roll=0.31)))
        self.assertFalse(roll_magazine_drop(300, StubRandom(roll=0.0)))

    def test_negative_ammunition_is_rejected(self):
        with self.assertRaises(ValueError):
            magazine_drop_chance(-1)


class MagazinePickupTests(unittest.TestCase):
    def test_pickup_is_collected_when_the_player_is_close(self):
        pickup = MagazinePickup(100.0, 100.0, 5)
        player = PlayerStub(110.0, 100.0)

        self.assertTrue(pickup.can_collect(player))

    def test_pickup_is_not_collected_from_far_away(self):
        pickup = MagazinePickup(100.0, 100.0, 5)
        player = PlayerStub(300.0, 100.0)

        self.assertFalse(pickup.can_collect(player))

    def test_invalid_pickup_values_are_rejected(self):
        with self.assertRaises(ValueError):
            MagazinePickup(0.0, 0.0, 0)
        with self.assertRaises(ValueError):
            MagazinePickup(0.0, 0.0, 5, radius=-1)


if __name__ == "__main__":
    unittest.main()
