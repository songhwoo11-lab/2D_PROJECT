import unittest
from unittest.mock import patch

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from game_state import GameState
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

    def test_escape_before_training_starts_is_ignored(self):
        self.scene.key_down("escape")

        self.assertEqual(self.scene.phase, "countdown")
        self.assertFalse(self.scene.paused)
        self.assertIsNone(self.scene.pending_action)

    def test_escape_during_training_opens_the_pause_menu(self):
        self.scene.phase = "playing"

        self.scene.key_down("escape")

        self.assertTrue(self.scene.paused)
        self.assertEqual(self.scene.pause_menu_index, 0)
        self.assertIsNone(self.scene.pending_action)

    def test_pause_freezes_the_timer_and_gun_input(self):
        self.scene.phase = "playing"
        self.scene.time_remaining = 42.0
        self.scene.mouse_held = True

        self.scene.key_down("escape")
        self.scene.update(5.0)

        self.assertEqual(self.scene.time_remaining, 42.0)
        self.assertEqual(self.scene.shots, 0)

    def test_escape_closes_the_pause_menu_after_release(self):
        self.scene.phase = "playing"
        self.scene.key_down("escape")
        self.scene.key_up("escape")

        self.scene.key_down("escape")

        self.assertFalse(self.scene.paused)
        self.assertIsNone(self.scene.pending_action)

    def test_gameplay_keys_are_ignored_while_paused(self):
        original_mode = self.scene.gun.fire_mode
        self.scene.phase = "playing"
        self.scene.key_down("escape")

        self.scene.key_down("e")

        self.assertEqual(self.scene.gun.fire_mode, original_mode)

    def test_pause_menu_navigation_wraps_around(self):
        self.scene.phase = "playing"
        self.scene.key_down("escape")

        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 1)
        self.scene.key_up("s")
        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 0)
        self.scene.key_up("s")
        self.scene.key_down("w")
        self.assertEqual(self.scene.pause_menu_index, 1)

    def test_mouse_hover_and_click_select_pause_menu_items(self):
        self.scene.phase = "playing"
        self.scene.key_down("escape")
        quit_y = SCREEN_HEIGHT / 2 + 44

        self.scene.mouse_move(SCREEN_WIDTH / 2, quit_y)
        self.assertEqual(self.scene.pause_menu_index, 1)
        self.scene.mouse_down("left", SCREEN_WIDTH / 2, quit_y)

        self.assertEqual(self.scene.pending_action, "return_to_lobby")
        self.assertFalse(self.scene.paused)

    def test_resume_option_continues_the_training(self):
        self.scene.phase = "playing"
        self.scene.key_down("escape")

        self.scene.key_down("space")

        self.assertFalse(self.scene.paused)
        self.assertIsNone(self.scene.pending_action)

    def test_quit_option_returns_to_lobby_without_a_record(self):
        state = GameState()
        scene = TrainingScene(state=state)
        scene.phase = "playing"
        scene._hits = 6
        scene.key_down("escape")
        scene.key_down("s")

        scene.key_down("space")

        self.assertEqual(scene.pending_action, "return_to_lobby")
        self.assertFalse(scene.paused)
        self.assertEqual(state.training_records, [])

    def test_pause_menu_draws_the_resume_and_quit_options(self):
        self.scene.phase = "playing"
        self.scene.paused = True
        self.scene.hud_font = object()
        rectangles = []

        with patch("training_scene.draw_centered_text") as draw_text:
            self.scene.draw(lambda *args: rectangles.append(args))

        labels = [call.args[2] for call in draw_text.call_args_list]
        self.assertIn("PAUSED", labels)
        self.assertIn("RESUME", labels)
        self.assertIn("QUIT TO LOBBY", labels)
        self.assertTrue(
            any(
                len(rectangle) >= 8 and rectangle[4:8] == (20, 25, 35, 225)
                for rectangle in rectangles
            )
        )

    def test_time_expiry_records_the_destroyed_target_count(self):
        state = GameState()
        scene = TrainingScene(state=state)
        scene.phase = "playing"
        scene.time_remaining = 0.0
        scene._hits = 6

        scene.update(0.0)

        self.assertEqual(len(state.training_records), 1)
        self.assertEqual(state.training_records[0].targets_destroyed, 6)

    def test_early_lobby_return_does_not_store_a_record(self):
        state = GameState()
        scene = TrainingScene(state=state)
        scene._hits = 6
        scene.phase = "playing"
        scene.key_down("escape")
        scene.key_down("s")

        scene.key_down("space")
        scene.update(1.0)

        self.assertEqual(scene.pending_action, "return_to_lobby")
        self.assertEqual(state.training_records, [])


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

    def test_aim_cursor_is_visible_only_while_playing_and_unpaused(self):
        self.assertFalse(self.scene.shows_aim_cursor)

        self.scene.phase = "playing"
        self.assertTrue(self.scene.shows_aim_cursor)

        self.scene.paused = True
        self.assertFalse(self.scene.shows_aim_cursor)

        self.scene.paused = False
        self.scene.phase = "finished"
        self.assertFalse(self.scene.shows_aim_cursor)

    def test_system_cursor_is_hidden_only_while_aiming(self):
        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.phase = "playing"
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.paused = True
        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.paused = False
        self.scene.phase = "finished"
        self.assertTrue(self.scene.shows_system_cursor)
