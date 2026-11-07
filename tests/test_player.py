import unittest

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

    def test_player_draws_injected_image_at_scaled_size(self):
        image = FakeImage()
        player = Player(100, 200, image=image, radius=12)

        player.draw()

        self.assertEqual(image.draw_calls, [(100.0, 200.0, 24.0, 24.0)])

    def test_player_draw_requires_an_image(self):
        with self.assertRaisesRegex(RuntimeError, "loaded player image"):
            Player(0, 0).draw()

    def test_player_moves_from_horizontal_and_vertical_input(self):
        player = Player(100, 200, speed=120)
        player.set_movement(1, -1, 0.5)

        player.update()

        self.assertEqual((player.x, player.y), (160.0, 140.0))

    def test_player_rejects_negative_delta_time(self):
        with self.assertRaisesRegex(ValueError, "delta_time"):
            Player(0, 0).set_movement(1, 0, -0.1)


if __name__ == "__main__":
    unittest.main()
