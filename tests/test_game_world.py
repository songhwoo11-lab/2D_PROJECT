import unittest

import game_world


class GameWorldTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()

    def tearDown(self):
        game_world.clear()

    def test_add_object_creates_requested_layer(self):
        obj = object()

        game_world.add_object(obj, depth=3)

        self.assertIn(obj, game_world.world[3])

    def test_negative_depth_is_rejected(self):
        with self.assertRaises(ValueError):
            game_world.add_object(object(), depth=-1)

    def test_objects_added_during_update_wait_until_next_tick(self):
        calls = []

        class Added:
            def update(self):
                calls.append("added")

            def draw(self):
                pass

        added = Added()

        class Adding:
            def update(self):
                calls.append("adding")
                game_world.add_object(added)

            def draw(self):
                pass

        game_world.add_object(Adding())
        game_world.update()
        self.assertEqual(calls, ["adding"])

        game_world.update()
        self.assertEqual(calls, ["adding", "adding", "added"])

    def test_removed_objects_are_not_visited_later_in_same_tick(self):
        calls = []

        class Removing:
            def update(self):
                game_world.remove_object(target)

            def draw(self):
                pass

        class Target:
            def update(self):
                calls.append("target")

            def draw(self):
                pass

        target = Target()
        game_world.add_object(Removing())
        game_world.add_object(target)

        game_world.update()

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
