import random
import unittest

from battle_scene import BattleScene
from enemy import Enemy, EnemyType
from game_config import WORLD_HEIGHT, WORLD_WIDTH
import game_world
from player import Player
from weapon import Gun
from waves import WaveDirector


class FakeBackground:
    def draw(self, *args):
        pass


class FakeImage:
    pass


class FakeFont:
    def draw(self, *args):
        pass


def make_scene(total_waves, spawn_rate):
    scene = BattleScene(
        Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
        Gun(),
        FakeBackground(),
        hud_font=FakeFont(),
        enemy_images={enemy_type: FakeImage() for enemy_type in EnemyType},
        enemy_draw_rectangle=lambda *args: None,
        enemy_draw_circle=lambda *args: None,
        random_source=random.Random(0),
    )
    scene.wave_director = WaveDirector(
        total_waves=total_waves,
        spawn_rate=spawn_rate,
        random_source=random.Random(0),
    )
    scene.spawn_warnings = []
    scene.waves_cleared = False
    scene._announce_wave()
    return scene


def alive_enemies():
    return [
        obj
        for layer in game_world.world
        for obj in layer
        if isinstance(obj, Enemy) and obj.is_alive
    ]


class BattleSceneWaveTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_battle_starts_without_spawned_enemies(self):
        self.assertEqual(alive_enemies(), [])
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(self.scene.wave_director.current_wave, 1)

    def test_spawning_creates_warnings_before_enemies(self):
        self.scene.update(0.1)

        self.assertEqual(len(self.scene.spawn_warnings), 100)
        self.assertEqual(alive_enemies(), [])

    def test_enemies_appear_after_warning_expires(self):
        self.scene.update(0.1)

        self.scene.update(0.5)

        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(len(alive_enemies()), 100)

    def test_clearing_every_enemy_finishes_the_last_wave(self):
        self.scene.update(0.1)
        self.scene.update(0.5)
        for enemy in alive_enemies():
            enemy.hp = 0

        self.scene.update(0.0)

        self.assertEqual(alive_enemies(), [])
        self.assertTrue(self.scene.waves_cleared)
        self.assertEqual(self.scene.wave_banner_text, "ALL WAVES CLEARED")

    def test_clearing_a_wave_advances_to_the_next_wave(self):
        scene = make_scene(total_waves=2, spawn_rate=1000)
        scene.update(0.1)
        scene.update(0.5)
        for enemy in alive_enemies():
            enemy.hp = 0

        scene.update(0.0)

        self.assertFalse(scene.waves_cleared)
        self.assertEqual(scene.wave_director.current_wave, 2)
        self.assertEqual(scene.wave_banner_text, "WAVE 2")

    def test_wave_enemies_use_the_wave_stat_multiplier(self):
        self.scene.wave_director.current_wave = 10

        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 500,
            self.scene.player.y,
        )

        self.assertEqual(enemy.max_hp, 40)
        self.assertEqual(enemy.attack_damage, 16)

    def test_reset_map_restores_the_first_wave(self):
        self.scene.update(0.1)
        self.scene.waves_cleared = True

        self.scene.reset_map()

        self.assertEqual(self.scene.wave_director.current_wave, 1)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertFalse(self.scene.waves_cleared)
        self.assertEqual(self.scene.wave_banner_text, "WAVE 1")
        self.assertEqual(alive_enemies(), [])


if __name__ == "__main__":
    unittest.main()
