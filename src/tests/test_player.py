import unittest
from unittest.mock import MagicMock

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


class PlayerHpTrailTests(unittest.TestCase):
    def test_damage_keeps_the_trailing_hp_during_the_delay(self):
        player = Player(0, 0)

        player.take_damage(30)
        player.update_hp_trail(0.1)

        self.assertEqual(player.hp, 70)
        self.assertEqual(player.hp_trail.value, 100)

    def test_trailing_hp_drains_towards_the_current_hp_after_the_delay(self):
        player = Player(0, 0)
        player.take_damage(30)
        player.update_hp_trail(player.hp_trail.delay)

        player.update_hp_trail(0.1)

        self.assertLess(player.hp_trail.value, 100)
        self.assertGreater(player.hp_trail.value, 70)

    def test_trailing_hp_stops_at_the_current_hp(self):
        player = Player(0, 0)
        player.take_damage(30)
        for _ in range(100):
            player.update_hp_trail(0.1)

        self.assertEqual(player.hp_trail.value, 70)

    def test_healing_snaps_the_trailing_hp_immediately(self):
        player = Player(0, 0)
        player.take_damage(30)
        player.update_hp_trail(player.hp_trail.delay)
        player.update_hp_trail(0.1)

        player.heal(10)
        player.update_hp_trail(0.0)

        self.assertEqual(player.hp, 80)
        self.assertEqual(player.hp_trail.value, 80)

    def test_reset_snaps_the_trailing_hp_to_maximum(self):
        player = Player(0, 0)
        player.take_damage(30)

        player.hp = player.max_hp
        player.reset_hp_trail()

        self.assertEqual(player.hp_trail.value, player.max_hp)


class PlayerDrawTests(unittest.TestCase):
    def test_draw_rotates_the_image_when_an_angle_is_given(self):
        image = MagicMock()
        player = Player(10, 20, image=image, radius=15)

        player.draw(angle=1.25)

        image.rotate_draw.assert_called_once_with(1.25, 10, 20, 30, 30)
        image.draw.assert_not_called()

    def test_draw_sets_and_restores_transparency(self):
        image = MagicMock()
        player = Player(10, 20, image=image, radius=15)

        player.draw(opacity=0.25)

        self.assertEqual(image.opacify.call_args_list[0].args, (0.25,))
        self.assertEqual(image.opacify.call_args_list[1].args, (1.0,))
        image.draw.assert_called_once_with(10, 20, 30, 30)

    def test_draw_scales_the_image_when_a_scale_is_given(self):
        image = MagicMock()
        player = Player(10, 20, image=image, radius=15)

        player.draw(scale=0.25)

        image.draw.assert_called_once_with(10, 20, 7.5, 7.5)


if __name__ == "__main__":
    unittest.main()
