import os
import unittest
from unittest.mock import patch

from dev_settings import GUN_ENV
from game_state import GameState
from main import GameApp
from weapon import (
    DEFAULT_GUN_ID,
    MACHINE_GUN_GUN_ID,
    RIFLE_GUN_ID,
    RIFLE,
    WeaponStates,
)


def make_app():
    app = GameApp()
    app.assets = {
        "lobby_background": None,
        "battle_background": None,
        "player_image": None,
        "gun_image": None,
        "bullet_image": None,
        "arrow_image": None,
        "ammo_image": None,
        "health_image": None,
        "hud_font": None,
        "hit_feedback_font": None,
        "debug_font": None,
        "enemy_images": {},
        "draw_rectangle": None,
        "draw_circle": None,
    }
    return app


class OwnershipAndSelectionTests(unittest.TestCase):
    def test_owned_guns_can_be_selected_normally(self):
        state = GameState(owned_guns=[DEFAULT_GUN_ID, RIFLE_GUN_ID])

        state.select_gun(RIFLE_GUN_ID)

        self.assertEqual(state.selected_gun, RIFLE_GUN_ID)

    def test_unowned_guns_cannot_be_selected_normally(self):
        state = GameState()

        with self.assertRaises(ValueError):
            state.select_gun(MACHINE_GUN_GUN_ID)

    def test_dev_gun_is_selected_without_ownership(self):
        state = GameState(dev_gun=MACHINE_GUN_GUN_ID)

        self.assertEqual(state.selected_gun, MACHINE_GUN_GUN_ID)
        self.assertFalse(state.owns_gun(MACHINE_GUN_GUN_ID))
        self.assertFalse(state.needs_gun_selection())

    def test_environment_dev_gun_reaches_the_game_state(self):
        with patch.dict(os.environ, {GUN_ENV: "rifle"}):
            state = GameState(owned_guns=[DEFAULT_GUN_ID, MACHINE_GUN_GUN_ID])

        self.assertEqual(state.selected_gun, RIFLE_GUN_ID)
        self.assertFalse(state.needs_gun_selection())

    def test_game_app_creates_the_dev_selected_battle_gun(self):
        app = make_app()
        app.state = GameState(dev_gun=RIFLE_GUN_ID)

        app.switch_scene("battle")

        self.assertIs(app.scene.gun.spec, RIFLE)


class WeaponSwitchStateTests(unittest.TestCase):
    def test_switching_back_restores_ammo_heat_and_reload_together(self):
        states = WeaponStates()
        states.gun.try_fire()
        states.gun.temperature = 120.0
        states.gun.reload_remaining = 1.5
        pistol_state = (
            states.gun.magazine_ammo,
            states.gun.reserve_ammo,
            states.gun.temperature,
            states.gun.reload_remaining,
        )

        states.select(RIFLE_GUN_ID)
        states.gun.temperature = 250.0
        states.gun.reload_remaining = 0.5

        states.select(DEFAULT_GUN_ID)

        self.assertEqual(
            (
                states.gun.magazine_ammo,
                states.gun.reserve_ammo,
                states.gun.temperature,
                states.gun.reload_remaining,
            ),
            pistol_state,
        )

        states.select(RIFLE_GUN_ID)

        self.assertEqual(states.gun.temperature, 250.0)
        self.assertEqual(states.gun.reload_remaining, 0.5)


if __name__ == "__main__":
    unittest.main()
