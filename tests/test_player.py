import unittest
import math

from player import Player


class FakeImage:
    def __init__(self):
        self.draw_calls = []

    def draw(self, *args):
        self.draw_calls.append(args)


class PlayerTests(unittest.TestCase):
    def test_player_initializes_core_state(self):
        player = Player(100, 200)

        self.assertEqual((player.x, player.y), (100.0, 200.0))
        self.assertEqual(player.hp, 100)
        self.assertEqual(player.max_hp, 100)
        self.assertEqual(player.aim_angle, 0.0)

    def test_aim_angle_tracks_mouse_direction(self):
        player = Player(100, 100)

        self.assertAlmostEqual(player.aim_at(200, 100), 0.0)
        self.assertAlmostEqual(player.aim_at(100, 200), math.pi / 2)
        self.assertAlmostEqual(player.aim_at(0, 100), math.pi)
        self.assertAlmostEqual(player.aim_at(100, 0), -math.pi / 2)

    def test_aim_at_player_position_keeps_last_direction(self):
        player = Player(100, 100)
        player.aim_at(100, 200)

        self.assertAlmostEqual(player.aim_at(100, 100), math.pi / 2)

    def test_player_draws_injected_image_at_scaled_size(self):
        image = FakeImage()
        player = Player(100, 200, image=image, radius=12)

        player.draw()

        self.assertEqual(image.draw_calls, [(100.0, 200.0, 24.0, 24.0)])

    def test_player_draw_requires_an_image(self):
        with self.assertRaisesRegex(RuntimeError, "loaded player image"):
            Player(0, 0).draw()

    def test_player_requires_positive_maximum_health(self):
        with self.assertRaisesRegex(ValueError, "max_hp"):
            Player(0, 0, max_hp=0)

    def test_player_moves_from_horizontal_input(self):
        player = Player(100, 200, speed=120)
        player.set_movement(1, 0, 0.5)

        player.update()

        self.assertEqual((player.x, player.y), (160.0, 200.0))

    def test_player_moves_from_vertical_input(self):
        player = Player(100, 200, speed=120)
        player.set_movement(0, -1, 0.5)

        player.update()

        self.assertEqual((player.x, player.y), (100.0, 140.0))

    def test_player_rejects_negative_delta_time(self):
        with self.assertRaisesRegex(ValueError, "delta_time"):
            Player(0, 0).set_movement(1, 0, -0.1)

    def test_diagonal_movement_is_normalized(self):
        horizontal = Player(1000, 1000, speed=120)
        diagonal = Player(1000, 1000, speed=120)
        horizontal.set_movement(1, 0, 1)
        diagonal.set_movement(1, 1, 1)

        horizontal.update()
        diagonal.update()

        self.assertAlmostEqual(math.hypot(horizontal.x - 1000, horizontal.y - 1000), 120)
        self.assertAlmostEqual(math.hypot(diagonal.x - 1000, diagonal.y - 1000), 120)

    def test_player_stays_inside_world_bounds(self):
        player = Player(20, 20, speed=1000, radius=10)
        player.set_movement(-1, -1, 1)
        player.update()
        self.assertEqual((player.x, player.y), (10, 10))

        player.x = 3180
        player.y = 2380
        player.set_movement(1, 1, 1)
        player.update()
        self.assertEqual((player.x, player.y), (3190, 2390))


if __name__ == "__main__":
    unittest.main()
