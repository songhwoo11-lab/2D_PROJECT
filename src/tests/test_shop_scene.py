import unittest

from shop_scene import ShopScene


class ShopSceneTests(unittest.TestCase):
    def setUp(self):
        self.scene = ShopScene()

    def tearDown(self):
        self.scene.close()

    def test_shop_scene_starts_without_a_pending_action(self):
        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)

    def test_update_and_draw_run_without_error(self):
        self.scene.update(1.0 / 60)
        self.scene.draw(lambda *args: None)

    def test_enter_key_asks_for_the_lobby_return(self):
        self.scene.key_down("space")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")

    def test_enter_key_is_not_triggered_twice(self):
        self.scene.key_down("space")
        self.scene.pending_action = None

        self.scene.key_down("space")

        self.assertIsNone(self.scene.pending_action)
