import unittest

from game_config import SCREEN_HEIGHT
from training_scene import TRAINING_CURSOR_ALPHA, TRAINING_CURSOR_COLOR, TrainingScene


class TrainingSceneTests(unittest.TestCase):
    def setUp(self):
        self.scene = TrainingScene()

    def tearDown(self):
        self.scene.close()

    def test_training_scene_starts_without_a_pending_action(self):
        self.assertIsNone(self.scene.pending_action)
        self.assertFalse(self.scene.exit_requested)

    def test_zero_shot_accuracy_is_zero(self):
        self.assertEqual(self.scene.shots, 0)
        self.assertEqual(self.scene.hits, 0)
        self.assertEqual(self.scene.misses, 0)
        self.assertEqual(self.scene.accuracy, 0.0)

    def test_update_and_draw_run_without_error(self):
        self.scene.update(1.0 / 60)
        self.scene.draw(lambda *args: None)

    def test_enter_key_asks_for_the_lobby_return(self):
        self.scene.key_down("escape")

        self.assertEqual(self.scene.pending_action, "return_to_lobby")


class TrainingCursorTests(unittest.TestCase):
    def setUp(self):
        self.scene = TrainingScene()
        self.rectangles = []

    def tearDown(self):
        self.scene.close()

    def _draw_cursor(self):
        self.scene._draw_aim_cursor(lambda *args: self.rectangles.append(args))
        return self.rectangles

    def test_cursor_position_follows_the_mouse(self):
        self.scene.mouse_move(300.0, 200.0)

        self.assertEqual(
            self.scene.aim_cursor_position,
            (300.0, SCREEN_HEIGHT - 200.0),
        )

    def test_cursor_is_drawn_as_four_segments_and_a_center_dot(self):
        self.scene.mouse_move(300.0, 200.0)

        rectangles = self._draw_cursor()

        self.assertEqual(len(rectangles), 5)

    def test_cursor_uses_a_dark_color_for_the_bright_training_ground(self):
        rectangles = self._draw_cursor()

        for rectangle in rectangles:
            self.assertEqual(rectangle[4:7], TRAINING_CURSOR_COLOR)
            self.assertEqual(rectangle[7], TRAINING_CURSOR_ALPHA)

    def test_cursor_moves_with_the_mouse(self):
        self.scene.mouse_move(300.0, 200.0)
        first = self._draw_cursor()
        first_center = (
            (first[0][0] + first[0][2]) / 2.0,
            (first[0][1] + first[0][3]) / 2.0,
        )

        self.rectangles = []
        self.scene.mouse_move(500.0, 300.0)
        second = self._draw_cursor()
        second_center = (
            (second[0][0] + second[0][2]) / 2.0,
            (second[0][1] + second[0][3]) / 2.0,
        )

        self.assertAlmostEqual(second_center[0] - first_center[0], 200.0)
        self.assertAlmostEqual(second_center[1] - first_center[1], -100.0)

    def test_cursor_is_drawn_with_the_scene(self):
        self.scene.mouse_move(300.0, 200.0)
        self.scene.phase = "playing"

        self.scene.draw(lambda *args: self.rectangles.append(args))

        self.assertEqual(len(self.rectangles), 6)

    def test_aim_cursor_is_visible_only_while_playing(self):
        self.assertFalse(self.scene.shows_aim_cursor)

        self.scene.phase = "playing"
        self.assertTrue(self.scene.shows_aim_cursor)

        self.scene.phase = "finished"
        self.assertFalse(self.scene.shows_aim_cursor)

    def test_system_cursor_is_hidden_only_while_aiming(self):
        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.phase = "playing"
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.phase = "finished"
        self.assertTrue(self.scene.shows_system_cursor)
