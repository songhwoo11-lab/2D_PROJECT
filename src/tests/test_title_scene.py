import unittest
from unittest import mock

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
import title_scene
from title_scene import (
    EXIT_GAME_ACTION,
    GAME_START_ACTION,
    RESET_GAME_ACTION,
    SETTINGS_ACTION,
    TITLE_ACTIONS,
    TITLE_BACKGROUND_COLOR,
    TITLE_BUTTON_COLOR,
    TITLE_BUTTON_HOVER_COLOR,
    TITLE_BUTTON_TEXT_COLOR,
    TitleScene,
    button_rect,
)


def click_button(scene, index):
    rect = button_rect(index)
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


class TitleLayoutTests(unittest.TestCase):
    def test_buttons_are_centered_and_listed_in_order(self):
        self.assertEqual(
            tuple(label for label, _ in TITLE_ACTIONS),
            ("Game Start", "Setting", "Reset Game", "Exit Game"),
        )
        for index in range(len(TITLE_ACTIONS)):
            rect = button_rect(index)
            self.assertEqual(
                (rect[0] + rect[2]) / 2,
                SCREEN_WIDTH / 2,
            )
        centers = [
            (button_rect(index)[1] + button_rect(index)[3]) / 2
            for index in range(len(TITLE_ACTIONS))
        ]
        self.assertEqual(sum(centers) / len(centers), SCREEN_HEIGHT / 2)

    def test_draw_uses_the_background_and_draws_every_button_label(self):
        background = mock.Mock()
        scene = TitleScene(background=background, hud_font=object())
        draw_rectangle = mock.Mock()

        with mock.patch("title_scene.draw_text_at_center") as draw_text:
            scene.draw(draw_rectangle)

        background.draw.assert_called_once_with(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
        self.assertEqual(draw_rectangle.call_count, len(TITLE_ACTIONS))
        self.assertEqual(
            [call.args[3] for call in draw_text.call_args_list],
            ["Game Start", "Setting", "Reset Game", "Exit Game"],
        )
        for call in draw_text.call_args_list:
            self.assertEqual(call.args[4], TITLE_BUTTON_TEXT_COLOR)

    def test_draw_falls_back_to_a_plain_background(self):
        scene = TitleScene(hud_font=None)
        draw_rectangle = mock.Mock()

        scene.draw(draw_rectangle)

        draw_rectangle.assert_called_once_with(
            0,
            0,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            *TITLE_BACKGROUND_COLOR,
            True,
        )

    def test_hovered_button_uses_the_highlight_color(self):
        scene = TitleScene(background=mock.Mock(), hud_font=object())
        scene.hover_index = 2
        draw_rectangle = mock.Mock()

        with mock.patch("title_scene.draw_text_at_center"):
            scene.draw(draw_rectangle)

        colors = [call.args[4:8] for call in draw_rectangle.call_args_list]
        self.assertEqual(
            colors,
            [
                TITLE_BUTTON_COLOR,
                TITLE_BUTTON_COLOR,
                TITLE_BUTTON_HOVER_COLOR,
                TITLE_BUTTON_COLOR,
            ],
        )


class TitleInputTests(unittest.TestCase):
    def test_each_button_requests_its_matching_action(self):
        scene = TitleScene()
        expected = (
            GAME_START_ACTION,
            SETTINGS_ACTION,
            RESET_GAME_ACTION,
            EXIT_GAME_ACTION,
        )

        for index, action in enumerate(expected):
            click_button(scene, index)
            self.assertEqual(scene.pending_action, action)
            scene.pending_action = None

    def test_clicking_outside_the_buttons_does_nothing(self):
        scene = TitleScene()

        scene.mouse_down("left", 1, 1)

        self.assertIsNone(scene.pending_action)
        self.assertEqual(scene.hover_index, 0)

    def test_mouse_move_updates_the_hovered_button(self):
        scene = TitleScene()
        rect = button_rect(3)
        center_x = (rect[0] + rect[2]) / 2
        canvas_y = (rect[1] + rect[3]) / 2

        scene.mouse_move(center_x, SCREEN_HEIGHT - canvas_y)

        self.assertEqual(scene.hover_index, 3)

        scene.mouse_move(1, 1)

        self.assertIsNone(scene.hover_index)

    def test_keyboard_can_select_and_activate_a_button(self):
        scene = TitleScene()

        scene.key_down("down")
        scene.key_up("down")
        scene.key_down("down")
        scene.key_up("down")
        self.assertEqual(scene.hover_index, 2)

        scene.key_down("return")

        self.assertEqual(scene.pending_action, RESET_GAME_ACTION)

    def test_keyboard_selection_wraps_around(self):
        scene = TitleScene()

        scene.key_down("up")

        self.assertEqual(scene.hover_index, len(TITLE_ACTIONS) - 1)

    def test_escape_does_not_request_an_exit_action(self):
        scene = TitleScene()

        scene.key_down("escape")

        self.assertIsNone(scene.pending_action)
        self.assertFalse(scene.exit_requested)

    def test_title_scene_has_no_audio_connection(self):
        scene = TitleScene()

        self.assertFalse(hasattr(scene, "audio"))


if __name__ == "__main__":
    unittest.main()
