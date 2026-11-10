import unittest

from battle_record import format_elapsed_time, result_record_text


class FormatElapsedTimeTests(unittest.TestCase):
    def test_zero_seconds(self):
        self.assertEqual(format_elapsed_time(0.0), "0:00.0")

    def test_seconds_are_padded(self):
        self.assertEqual(format_elapsed_time(5.25), "0:05.2")

    def test_minutes_roll_over(self):
        self.assertEqual(format_elapsed_time(65.0), "1:05.0")

    def test_large_times_keep_counting_minutes(self):
        self.assertEqual(format_elapsed_time(3725.5), "62:05.5")

    def test_negative_time_is_rejected(self):
        with self.assertRaises(ValueError):
            format_elapsed_time(-1.0)


class ResultRecordTextTests(unittest.TestCase):
    def test_victory_shows_the_clear_time(self):
        text = result_record_text(
            "victory",
            reached_wave=30,
            total_waves=30,
            elapsed_time=120.0,
            clear_time=100.0,
        )

        self.assertEqual(text, "CLEAR TIME 1:40.0")

    def test_victory_without_clear_time_uses_elapsed_time(self):
        text = result_record_text(
            "victory",
            reached_wave=30,
            total_waves=30,
            elapsed_time=90.0,
        )

        self.assertEqual(text, "CLEAR TIME 1:30.0")

    def test_defeat_shows_the_reached_wave(self):
        text = result_record_text(
            "defeat",
            reached_wave=7,
            total_waves=30,
            elapsed_time=50.0,
        )

        self.assertEqual(text, "REACHED WAVE 7/30")

    def test_quit_shows_the_reached_wave(self):
        text = result_record_text(
            "quit",
            reached_wave=12,
            total_waves=30,
            elapsed_time=50.0,
        )

        self.assertEqual(text, "REACHED WAVE 12/30")


if __name__ == "__main__":
    unittest.main()
