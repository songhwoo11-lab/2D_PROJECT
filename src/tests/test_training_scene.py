import unittest

from training_scene import TrainingScene


class TrainingSceneTests(unittest.TestCase):
    def setUp(self):
        self.scene = TrainingScene()

    def tearDown(self):
        self.scene.close()

    def test_training_scene_starts_without_a_pending_action(self):
        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)

    def test_update_and_draw_run_without_error(self):
        self.scene.update(1.0 / 60)
        self.scene.draw(lambda *args: None)

    def test_enter_key_asks_for_the_lobby_return(self):
        self.scene.key_down("return")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")
