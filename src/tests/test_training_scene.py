import unittest
from unittest.mock import call, patch

from audio import TRAINING_MUSIC_FILE
from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
from game_state import GameState
from training_scene import (
    EXIT_BUTTON_COLOR,
    EXIT_BUTTON_LABEL,
    EXIT_BUTTON_TEXT_COLOR,
    TRAINING_CURSOR_ALPHA,
    TRAINING_CURSOR_COLOR,
    TrainingScene,
    exit_button_rect,
)


class SequenceRandom:
    def __init__(self, values):
        self.values = iter(values)

    def uniform(self, low, high):
        return next(self.values)


class RecordingAudio:
    def __init__(self):
        self.events = []
        self.paused = False

    def play(self, name):
        self.events.append(("play", name))

    def pause(self):
        self.events.append(("pause",))
        self.paused = True
        return True

    def resume(self):
        self.events.append(("resume",))
        self.paused = False
        return True

    def stop(self):
        self.events.append(("stop",))
        self.paused = False


def exit_button_screen_center():
    left, bottom, right, top = exit_button_rect()
    return (left + right) / 2, SCREEN_HEIGHT - (bottom + top) / 2


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

    def test_training_title_is_not_drawn(self):
        self.scene.hud_font = object()

        with patch("training_scene.draw_centered_text") as draw_text, patch(
            "training_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: None)

        labels = [call.args[2] for call in draw_text.call_args_list]
        self.assertNotIn("TRAINING", labels)

    def test_top_time_display_shows_only_the_number(self):
        self.scene.hud_font = object()
        self.scene.phase = "playing"
        self.scene.time_remaining = 42.0

        with patch("training_scene.draw_centered_text") as draw_text, patch(
            "training_scene.draw_text_at_center"
        ):
            self.scene.draw(lambda *args: None)

        labels = [call.args[2] for call in draw_text.call_args_list]
        self.assertIn("42", labels)
        self.assertNotIn("TIME 42", labels)

    def test_target_is_hidden_before_training_starts(self):
        with patch.object(self.scene.target, "draw") as draw_target:
            self.scene.draw(lambda *args: None)

        draw_target.assert_not_called()

    def test_target_appears_as_soon_as_training_starts(self):
        self.scene.update(3.0)
        self.assertEqual(self.scene.phase, "playing")

        with patch.object(self.scene.target, "draw") as draw_target:
            self.scene.draw(lambda *args: None)

        draw_target.assert_called_once()

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

        with patch("training_scene.draw_centered_text") as draw_text, patch(
            "training_scene.draw_text_at_center"
        ):
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

    def test_exit_button_opens_the_pause_menu(self):
        self.scene.phase = "playing"
        screen_x, screen_y = exit_button_screen_center()
        self.scene.mouse_held = True

        self.scene.mouse_down("left", screen_x, screen_y)

        self.assertTrue(self.scene.paused)
        self.assertEqual(self.scene.pause_menu_index, 0)
        self.assertFalse(self.scene.mouse_held)
        self.assertIsNone(self.scene.pending_action)

    def test_hidden_exit_button_is_not_clickable_during_the_countdown(self):
        screen_x, screen_y = exit_button_screen_center()

        self.scene.mouse_down("left", screen_x, screen_y)

        self.assertFalse(self.scene.paused)
        self.assertTrue(self.scene.mouse_held)

    def test_exit_button_is_drawn_in_the_bottom_right(self):
        self.scene.phase = "playing"
        self.scene.hud_font = object()
        rectangles = []
        left, bottom, right, top = exit_button_rect()

        with patch("training_scene.draw_centered_text"), patch(
            "training_scene.draw_text_at_center"
        ) as text_at_center:
            self.scene.draw(lambda *args: rectangles.append(args))

        self.assertIn(
            (left, bottom, right, top, *EXIT_BUTTON_COLOR, True),
            rectangles,
        )
        text_at_center.assert_any_call(
            self.scene.hud_font,
            (left + right) / 2,
            (bottom + top) / 2,
            EXIT_BUTTON_LABEL,
            EXIT_BUTTON_TEXT_COLOR,
        )

    def test_exit_button_is_not_drawn_before_training_starts(self):
        self.scene.hud_font = object()
        rectangles = []
        left, bottom, right, top = exit_button_rect()

        with patch("training_scene.draw_centered_text"), patch(
            "training_scene.draw_text_at_center"
        ) as text_at_center:
            self.scene.draw(lambda *args: rectangles.append(args))

        self.assertNotIn(
            (left, bottom, right, top, *EXIT_BUTTON_COLOR, True),
            rectangles,
        )
        text_at_center.assert_not_called()

    def test_target_does_not_appear_over_the_exit_button(self):
        self.scene.phase = "playing"
        self.scene.target.x = (exit_button_rect()[0] + exit_button_rect()[2]) / 2
        self.scene.target.y = (exit_button_rect()[1] + exit_button_rect()[3]) / 2

        with patch.object(self.scene.target, "draw") as draw_target:
            self.scene.draw(lambda *args: None)

        draw_target.assert_not_called()

    def test_target_respawn_avoids_the_exit_button_area(self):
        left, bottom, right, top = exit_button_rect()
        exit_x = (left + right) / 2
        exit_y = (bottom + top) / 2
        self.scene.random_source = SequenceRandom(
            [exit_x, exit_y, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2]
        )

        self.scene._respawn_target()

        self.assertAlmostEqual(self.scene.target.x, SCREEN_WIDTH / 2)
        self.assertAlmostEqual(self.scene.target.y, SCREEN_HEIGHT / 2)

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


class TrainingSceneMusicTests(unittest.TestCase):
    def make_scene(self):
        audio = RecordingAudio()
        return TrainingScene(audio=audio), audio

    def test_music_starts_after_the_three_second_countdown(self):
        scene, audio = self.make_scene()

        self.assertEqual(audio.events, [])
        scene.update(2.9)
        self.assertEqual(audio.events, [])

        scene.update(0.2)

        self.assertEqual(audio.events, [("play", TRAINING_MUSIC_FILE)])

    def test_pause_resumes_music_without_restarting_it(self):
        scene, audio = self.make_scene()
        scene.update(3.0)
        audio.events.clear()

        scene.key_down("escape")
        self.assertEqual(audio.events, [("pause",)])
        self.assertTrue(audio.paused)

        scene.key_up("escape")
        scene.key_down("escape")

        self.assertEqual(audio.events, [("pause",), ("resume",)])
        self.assertFalse(audio.paused)

    def test_resume_menu_item_resumes_music_without_restarting_it(self):
        scene, audio = self.make_scene()
        scene.update(3.0)
        audio.events.clear()

        scene.key_down("escape")
        scene.key_down("space")

        self.assertEqual(audio.events, [("pause",), ("resume",)])
        self.assertFalse(audio.paused)

    def test_finishing_training_stops_music(self):
        scene, audio = self.make_scene()
        scene.update(3.0)
        audio.events.clear()

        scene.time_remaining = 0.0
        scene.update(0.0)

        self.assertEqual(audio.events, [("stop",)])

    def test_quit_to_lobby_stops_music(self):
        scene, audio = self.make_scene()
        scene.update(3.0)
        audio.events.clear()

        scene.key_down("q")

        self.assertEqual(audio.events, [("stop",)])


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

    def test_cursor_is_drawn_immediately_when_the_scene_starts(self):
        self.scene.mouse_move(300.0, 200.0)
        self.assertEqual(self.scene.phase, "countdown")

        self.scene.draw(lambda *args: self.rectangles.append(args))

        self.assertEqual(len(self.rectangles), 6)

    def test_aim_cursor_is_visible_immediately_and_only_hidden_while_paused(self):
        self.assertTrue(self.scene.shows_aim_cursor)

        self.scene.phase = "playing"
        self.assertTrue(self.scene.shows_aim_cursor)

        self.scene.paused = True
        self.assertFalse(self.scene.shows_aim_cursor)

        self.scene.paused = False
        self.scene.phase = "finished"
        self.assertTrue(self.scene.shows_aim_cursor)

    def test_system_cursor_is_hidden_immediately_and_shown_only_while_paused(self):
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.phase = "playing"
        self.assertFalse(self.scene.shows_system_cursor)

        self.scene.paused = True
        self.assertTrue(self.scene.shows_system_cursor)

        self.scene.paused = False
        self.scene.phase = "finished"
        self.assertFalse(self.scene.shows_system_cursor)
