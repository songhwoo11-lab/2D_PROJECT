import unittest

from game_camera import Camera
from game_config import MAP_SCALE, SCREEN_HEIGHT, SCREEN_WIDTH, WORLD_HEIGHT, WORLD_WIDTH


class CameraTests(unittest.TestCase):
    def test_world_dimensions_are_twice_the_screen_dimensions(self):
        self.assertEqual(MAP_SCALE, 2)
        self.assertEqual(WORLD_WIDTH, SCREEN_WIDTH * 2)
        self.assertEqual(WORLD_HEIGHT, SCREEN_HEIGHT * 2)

    def test_follow_centers_on_target_inside_world(self):
        camera = Camera()

        camera.follow(800, 600)

        self.assertEqual((camera.x, camera.y), (400, 300))
        self.assertEqual(camera.world_to_screen(800, 600), (400, 300))

    def test_follow_clamps_at_world_edges(self):
        camera = Camera()

        camera.follow(0, 0)
        self.assertEqual((camera.x, camera.y), (0, 0))

        camera.follow(WORLD_WIDTH, WORLD_HEIGHT)
        self.assertEqual((camera.x, camera.y), (800, 600))

    def test_mouse_top_origin_converts_to_world_coordinates(self):
        camera = Camera()
        camera.follow(800, 600)

        self.assertEqual(camera.screen_to_world(400, 300, origin_top=True), (800, 600))
        self.assertEqual(camera.screen_to_world(20, 40, origin_top=True), (420, 860))


if __name__ == "__main__":
    unittest.main()
