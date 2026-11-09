import math
import unittest

import game_world
from arrow import Arrow
from game_config import ARROW_HIT_RADIUS, ARROW_SIZE
from player import Player


class FakeImage:
    def __init__(self):
        self.calls = []

    def rotate_draw(self, *args):
        self.calls.append(args)


class ArrowTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_arrow_draws_toward_target_with_arrow_sprite(self):
        image = FakeImage()
        arrow = Arrow(0, 0, 100, 0, image)
        arrow.set_screen_position(40, 50)

        arrow.draw()

        angle, x, y, width, height = image.calls[0]
        self.assertAlmostEqual(angle, -3 * math.pi / 4)
        self.assertEqual((x, y, width, height), (40, 50, ARROW_SIZE, ARROW_SIZE))

    def test_arrow_moves_toward_target_and_removes_at_impact(self):
        arrow = Arrow(0, 0, 100, 0, FakeImage(), speed=600)
        game_world.add_object(arrow, depth=2)

        arrow.update()
        self.assertAlmostEqual(arrow.x, 10)
        self.assertIn(arrow, game_world.world[2])

        arrow.update()
        self.assertAlmostEqual(arrow.x, 20)
        self.assertIn(arrow, game_world.world[2])
        for _ in range(10):
            arrow.update()
        arrow.update()
        self.assertNotIn(arrow, game_world.world[2])

    def test_arrow_only_damages_player_when_its_path_hits(self):
        player = Player(100, 0, radius=10)
        arrow = Arrow(
            0,
            0,
            100,
            0,
            FakeImage(),
            speed=600,
            target=player,
            damage=10,
        )
        game_world.add_object(arrow, depth=2)

        while arrow in game_world.world[2]:
            arrow.update()

        self.assertEqual(player.hp, 90)

    def test_arrow_misses_player_who_moves_out_of_its_path(self):
        player = Player(100, 0, radius=10)
        arrow = Arrow(
            0,
            0,
            100,
            0,
            FakeImage(),
            speed=600,
            target=player,
            damage=10,
        )
        game_world.add_object(arrow, depth=2)
        player.y = player.radius + ARROW_HIT_RADIUS + 0.1

        while arrow in game_world.world[2]:
            arrow.update()

        self.assertEqual(player.hp, player.max_hp)

    def test_arrow_rejects_missing_image_when_drawn(self):
        with self.assertRaisesRegex(RuntimeError, "loaded arrow image"):
            Arrow(0, 0, 100, 0, None).draw()


if __name__ == "__main__":
    unittest.main()
