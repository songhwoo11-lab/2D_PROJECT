import random
import unittest

from game_config import PICKUP_DRAW_SIZE
from pickup import (
    HealthPickup,
    MagazinePickup,
    health_drop_chance,
    magazine_drop_chance,
    roll_coin_reward,
    roll_health_drop,
    roll_magazine_drop,
)


class FakeImage:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, w=None, h=None):
        self.draws.append((x, y, w, h))


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


class PickupImageTests(unittest.TestCase):
    def test_pickup_draws_its_image_centered_on_the_screen_position(self):
        image = FakeImage()
        pickup = MagazinePickup(100.0, 100.0, 5, image=image)

        drawn = pickup.draw(40.0, 60.0)

        self.assertTrue(drawn)
        self.assertEqual(image.draws, [(40.0, 60.0, PICKUP_DRAW_SIZE, PICKUP_DRAW_SIZE)])

    def test_health_pickup_draws_its_image(self):
        image = FakeImage()
        pickup = HealthPickup(100.0, 100.0, image=image)

        drawn = pickup.draw(10.0, 20.0)

        self.assertTrue(drawn)
        self.assertEqual(len(image.draws), 1)

    def test_pickup_without_image_draws_nothing(self):
        pickup = MagazinePickup(100.0, 100.0, 5)

        self.assertFalse(pickup.draw(10.0, 20.0))


class HealthDropChanceTests(unittest.TestCase):
    def test_chance_equals_the_missing_hp_ratio(self):
        self.assertEqual(health_drop_chance(100, 100), 0.0)
        self.assertAlmostEqual(health_drop_chance(90, 100), 0.1)
        self.assertAlmostEqual(health_drop_chance(25, 100), 0.75)
        self.assertEqual(health_drop_chance(0, 100), 1.0)

    def test_chance_is_clamped_to_zero_and_one(self):
        self.assertEqual(health_drop_chance(150, 100), 0.0)
        self.assertEqual(health_drop_chance(-10, 100), 1.0)

    def test_drop_roll_uses_the_missing_hp_chance(self):
        self.assertTrue(roll_health_drop(50, 100, StubRandom(roll=0.49)))
        self.assertFalse(roll_health_drop(50, 100, StubRandom(roll=0.51)))
        self.assertFalse(roll_health_drop(100, 100, StubRandom(roll=0.0)))

    def test_invalid_max_hp_is_rejected(self):
        with self.assertRaises(ValueError):
            health_drop_chance(10, 0)


class HealthPickupTests(unittest.TestCase):
    def test_health_pickup_heals_ten_by_default(self):
        pickup = HealthPickup(100.0, 100.0)

        self.assertEqual(pickup.amount, 10)

    def test_health_pickup_uses_the_shared_collection_range(self):
        pickup = HealthPickup(100.0, 100.0)
        player = PlayerStub(110.0, 100.0)

        self.assertTrue(pickup.can_collect(player))

    def test_invalid_health_pickup_values_are_rejected(self):
        with self.assertRaises(ValueError):
            HealthPickup(0.0, 0.0, amount=0)
        with self.assertRaises(ValueError):
            HealthPickup(0.0, 0.0, radius=-1)


if __name__ == "__main__":
    unittest.main()
