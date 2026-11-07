import unittest

from game_camera import Camera


class CameraTests(unittest.TestCase):
    def test_follow_centers_on_target_inside_world(self):
        camera = Camera()

        camera.follow(1600, 1200)

        self.assertEqual((camera.x, camera.y), (1200, 900))
        self.assertEqual(camera.world_to_screen(1600, 1200), (400, 300))

    def test_follow_clamps_at_world_edges(self):
        camera = Camera()

        camera.follow(0, 0)
        self.assertEqual((camera.x, camera.y), (0, 0))

        camera.follow(3200, 2400)
        self.assertEqual((camera.x, camera.y), (2400, 1800))

    def test_mouse_top_origin_converts_to_world_coordinates(self):
        camera = Camera()
        camera.follow(1600, 1200)

        self.assertEqual(camera.screen_to_world(400, 300, origin_top=True), (1600, 1200))
        self.assertEqual(camera.screen_to_world(20, 40, origin_top=True), (1220, 1460))


if __name__ == "__main__":
    unittest.main()
