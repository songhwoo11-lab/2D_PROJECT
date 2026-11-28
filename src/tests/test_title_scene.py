import unittest
from unittest import mock

from game_config import SCREEN_HEIGHT, SCREEN_WIDTH
import title_scene
from title_scene import (
    EXIT_GAME_ACTION,
    GAME_START_ACTION,
    RESET_BUTTON_INDEX,
    RESET_COMPLETE_SECONDS,
    RESET_COMPLETE_TITLE,
    RESET_DIALOG_NO_RECT,
    RESET_DIALOG_TEXT_COLOR,
    RESET_DIALOG_TITLE,
    RESET_DIALOG_TITLE_Y,
    RESET_DIALOG_YES_RECT,
    RESET_GAME_ACTION,
    SETTINGS_ACTION,
    TITLE_ACTIONS,
    TITLE_BACKGROUND_COLOR,
    TITLE_BUTTON_CENTER_Y,
    TITLE_BUTTON_COLOR,
    TITLE_BUTTON_FIRST_TOP,
    TITLE_BUTTON_HOVER_COLOR,
    TITLE_BUTTON_TEXT_COLOR,
    TITLE_BUTTON_TOP_GAP,
    TITLE_LOGO_HEIGHT,
    TITLE_LOGO_TOP_MARGIN,
    TITLE_LOGO_WIDTH,
    TitleScene,
    button_rect,
    logo_center,
)


def click_button(scene, index):
    rect = button_rect(index)
    center_x = (rect[0] + rect[2]) / 2
    canvas_y = (rect[1] + rect[3]) / 2
    scene.mouse_down("left", center_x, SCREEN_HEIGHT - canvas_y)


def click_dialog_button(scene, rect):
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
        self.assertEqual(sum(centers) / len(centers), TITLE_BUTTON_CENTER_Y)

    def test_buttons_are_below_the_logo_without_overlapping_it(self):
        _, logo_y = logo_center()
        logo_bottom = logo_y - TITLE_LOGO_HEIGHT / 2
        first_top = button_rect(0)[3]
        last_bottom = button_rect(len(TITLE_ACTIONS) - 1)[1]

        self.assertEqual(first_top, TITLE_BUTTON_FIRST_TOP)
        self.assertEqual(first_top, logo_bottom - TITLE_BUTTON_TOP_GAP)
        self.assertLess(first_top, logo_bottom)
        self.assertGreaterEqual(last_bottom, 0)

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

    def test_logo_is_drawn_at_the_top_center(self):
        logo = mock.Mock()
        scene = TitleScene(background=mock.Mock(), logo=logo, hud_font=object())
        draw_rectangle = mock.Mock()

        with mock.patch("title_scene.draw_text_at_center"):
            scene.draw(draw_rectangle)

        logo.draw.assert_called_once_with(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - TITLE_LOGO_TOP_MARGIN - TITLE_LOGO_HEIGHT / 2,
            TITLE_LOGO_WIDTH,
            TITLE_LOGO_HEIGHT,
        )
        self.assertEqual(
            logo_center(),
            (
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT - TITLE_LOGO_TOP_MARGIN - TITLE_LOGO_HEIGHT / 2,
            ),
        )

    def test_draw_without_a_logo_is_safe(self):
        scene = TitleScene(background=mock.Mock(), hud_font=object())

        with mock.patch("title_scene.draw_text_at_center"):
            scene.draw(mock.Mock())

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
            if action == RESET_GAME_ACTION:
                self.assertEqual(scene.mode, "confirm")
                self.assertIsNone(scene.pending_action)
                scene.mode = "menu"
            else:
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

        self.assertEqual(scene.mode, "confirm")
        self.assertIsNone(scene.pending_action)

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


class TitleResetDialogTests(unittest.TestCase):
    def make_dialog_scene(self):
        return TitleScene(background=mock.Mock(), hud_font=object())

    def test_reset_button_opens_the_confirmation_and_blocks_the_menu(self):
        scene = TitleScene()

        click_button(scene, RESET_BUTTON_INDEX)
        click_button(scene, 0)

        self.assertEqual(scene.mode, "confirm")
        self.assertIsNone(scene.pending_action)

    def test_confirmation_draws_the_title_and_yes_no_buttons(self):
        scene = self.make_dialog_scene()
        scene.logo = mock.Mock()
        scene.mode = "confirm"
        draw_rectangle = mock.Mock()

        with mock.patch("title_scene.draw_centered_text") as centered, mock.patch(
            "title_scene.draw_text_at_center"
        ) as at_center:
            scene.draw(draw_rectangle)

        centered.assert_called_once_with(
            scene.hud_font,
            RESET_DIALOG_TITLE_Y,
            RESET_DIALOG_TITLE,
            RESET_DIALOG_TEXT_COLOR,
        )
        self.assertEqual(
            [call.args[3] for call in at_center.call_args_list],
            [label for label, _ in TITLE_ACTIONS] + ["YES", "NO"],
        )
        rects = [call.args[:4] for call in draw_rectangle.call_args_list]
        for index in range(len(TITLE_ACTIONS)):
            self.assertIn(button_rect(index), rects)
        self.assertIn(RESET_DIALOG_YES_RECT, rects)
        self.assertIn(RESET_DIALOG_NO_RECT, rects)
        self.assertNotIn((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), rects)
        self.assertEqual(draw_rectangle.call_count, len(TITLE_ACTIONS) + 3)
        scene.background.draw.assert_called_once()
        scene.logo.draw.assert_called_once()

    def test_yes_requests_the_reset_action(self):
        scene = TitleScene()

        click_button(scene, RESET_BUTTON_INDEX)
        click_dialog_button(scene, RESET_DIALOG_YES_RECT)

        self.assertEqual(scene.pending_action, RESET_GAME_ACTION)

    def test_no_returns_to_the_menu(self):
        scene = TitleScene()

        click_button(scene, RESET_BUTTON_INDEX)
        click_dialog_button(scene, RESET_DIALOG_NO_RECT)

        self.assertEqual(scene.mode, "menu")
        self.assertIsNone(scene.pending_action)

    def test_escape_closes_the_confirmation(self):
        scene = TitleScene()

        click_button(scene, RESET_BUTTON_INDEX)
        scene.key_down("escape")

        self.assertEqual(scene.mode, "menu")
        self.assertIsNone(scene.pending_action)

    def test_completion_dialog_shows_a_message_then_returns_to_the_menu(self):
        scene = self.make_dialog_scene()
        scene.logo = mock.Mock()
        scene.show_reset_complete()
        draw_rectangle = mock.Mock()

        with mock.patch("title_scene.draw_centered_text") as centered, mock.patch(
            "title_scene.draw_text_at_center"
        ) as at_center:
            scene.draw(draw_rectangle)

        self.assertEqual(scene.mode, "complete")
        self.assertEqual(scene.reset_complete_remaining, RESET_COMPLETE_SECONDS)
        centered.assert_called_once_with(
            scene.hud_font,
            RESET_DIALOG_TITLE_Y,
            RESET_COMPLETE_TITLE,
            RESET_DIALOG_TEXT_COLOR,
        )
        self.assertEqual(
            [call.args[3] for call in at_center.call_args_list],
            [label for label, _ in TITLE_ACTIONS],
        )
        rects = [call.args[:4] for call in draw_rectangle.call_args_list]
        for index in range(len(TITLE_ACTIONS)):
            self.assertIn(button_rect(index), rects)
        self.assertNotIn((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), rects)
        self.assertEqual(draw_rectangle.call_count, len(TITLE_ACTIONS) + 1)
        scene.background.draw.assert_called_once()
        scene.logo.draw.assert_called_once()

        scene.update(RESET_COMPLETE_SECONDS)

        self.assertEqual(scene.mode, "menu")

    def test_completion_dialog_can_be_dismissed_by_click_or_key(self):
        scene = TitleScene()

        scene.show_reset_complete()
        click_dialog_button(scene, RESET_DIALOG_YES_RECT)
        self.assertEqual(scene.mode, "menu")

        scene.show_reset_complete()
        scene.key_down("return")
        self.assertEqual(scene.mode, "menu")


if __name__ == "__main__":
    unittest.main()
