import random
import unittest

from battle_scene import BattleResult, BattleScene
from enemy import Enemy, EnemyType
from game_config import PICKUP_DRAW_SIZE, WORLD_HEIGHT, WORLD_WIDTH
import game_world
from player import Player
from pickup import HealthPickup, MagazinePickup
from weapon import Gun
from waves import WaveDirector


class FakeBackground:
    def draw(self, *args):
        pass


class FakeImage:
    def __init__(self):
        self.draws = []

    def draw(self, x, y, w=None, h=None):
        self.draws.append((x, y, w, h))


class FakeFont:
    def draw(self, *args):
        pass


class StubRandom:
    def __init__(self, coin=1, roll=1.0):
        self.coin = coin
        self.roll = roll

    def randint(self, minimum, maximum):
        return self.coin

    def random(self):
        return self.roll


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
        self.assertEqual(scene.reached_wave, 2)
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
        self.scene.coins = 12
        self.scene.pickups.append(
            MagazinePickup(self.scene.player.x, self.scene.player.y, 5)
        )

        self.scene.reset_map()

        self.assertEqual(self.scene.wave_director.current_wave, 1)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertFalse(self.scene.waves_cleared)
        self.assertEqual(self.scene.wave_banner_text, "WAVE 1")
        self.assertEqual(alive_enemies(), [])
        self.assertEqual(self.scene.coins, 0)
        self.assertEqual(self.scene.pickups, [])


class BattleSceneRewardTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_defeating_an_enemy_awards_coins_and_can_drop_a_magazine(self):
        self.scene.random_source = StubRandom(coin=4, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(self.scene.coins, 4)
        self.assertEqual(len(self.scene.pickups), 1)
        self.assertEqual(self.scene.pickups[0].amount, 10)

    def test_no_magazine_drops_at_three_hundred_or_more_ammo(self):
        self.scene.random_source = StubRandom(coin=2, roll=0.0)
        self.scene.gun.magazine_ammo = 10
        self.scene.gun.reserve_ammo = 290

        self._defeat_one_enemy()

        self.assertEqual(self.scene.coins, 2)
        self.assertEqual(self.scene.pickups, [])

    def test_walking_over_a_magazine_adds_reserve_ammo(self):
        self.scene.gun.magazine_ammo = 2
        self.scene.gun.reserve_ammo = 40
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
            )
        )

        self.scene._update_pickups()

        self.assertEqual(self.scene.gun.magazine_ammo, 2)
        self.assertEqual(self.scene.gun.reserve_ammo, 50)
        self.assertEqual(self.scene.pickups, [])

    def test_full_magazine_still_takes_the_pickup(self):
        self.scene.gun.magazine_ammo = self.scene.gun.spec.magazine_size
        self.scene.gun.reserve_ammo = 40
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
            )
        )

        self.scene._update_pickups()

        self.assertEqual(
            self.scene.gun.magazine_ammo,
            self.scene.gun.spec.magazine_size,
        )
        self.assertEqual(self.scene.gun.reserve_ammo, 50)
        self.assertEqual(len(self.scene.pickups), 0)


class BattleScenePickupImageTests(unittest.TestCase):
    def setUp(self):
        self.ammo_image = FakeImage()
        self.health_image = FakeImage()
        self.scene = make_scene(total_waves=1, spawn_rate=1000)
        self.scene.ammo_image = self.ammo_image
        self.scene.health_image = self.health_image

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_magazine_drop_uses_the_ammo_image(self):
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.pickups), 1)
        self.assertIs(self.scene.pickups[0].image, self.ammo_image)

    def test_health_drop_uses_the_health_image(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertIs(self.scene.health_pickups[0].image, self.health_image)

    def test_pickups_are_drawn_with_their_images(self):
        self.scene.pickups.append(
            MagazinePickup(
                self.scene.player.x,
                self.scene.player.y,
                10,
                image=self.ammo_image,
            )
        )
        self.scene.health_pickups.append(
            HealthPickup(
                self.scene.player.x,
                self.scene.player.y,
                image=self.health_image,
            )
        )
        rectangles = []

        self.scene._draw_pickups(
            lambda x1, y1, x2, y2, *args: rectangles.append((x1, y1, x2, y2))
        )

        self.assertEqual(len(self.ammo_image.draws), 1)
        self.assertEqual(len(self.health_image.draws), 1)
        self.assertEqual(rectangles, [])

    def test_pickup_images_are_drawn_at_the_pickup_position(self):
        pickup = MagazinePickup(
            self.scene.player.x,
            self.scene.player.y,
            10,
            image=self.ammo_image,
        )
        self.scene.pickups.append(pickup)

        self.scene._draw_pickups(lambda *args: None)

        screen_x, screen_y, width, height = self.ammo_image.draws[0]
        expected_x, expected_y = self.scene.camera.world_to_screen(
            self.scene.player.x,
            self.scene.player.y,
        )
        self.assertAlmostEqual(screen_x, expected_x)
        self.assertAlmostEqual(screen_y, expected_y)
        self.assertEqual(width, PICKUP_DRAW_SIZE)
        self.assertEqual(height, PICKUP_DRAW_SIZE)

    def test_pickup_without_image_falls_back_to_a_rectangle(self):
        self.scene.pickups.append(
            MagazinePickup(self.scene.player.x, self.scene.player.y, 10)
        )
        rectangles = []

        self.scene._draw_pickups(
            lambda x1, y1, x2, y2, *args: rectangles.append((x1, y1, x2, y2))
        )

        self.assertEqual(len(rectangles), 1)


class BattleSceneHealthDropTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def _defeat_one_enemy(self):
        enemy = self.scene._spawn_wave_enemy(
            EnemyType.BASIC,
            self.scene.player.x + 300,
            self.scene.player.y,
        )
        enemy.hp = 0
        self.scene.update(0.0)

    def test_damaged_player_can_receive_a_health_drop(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 1)
        self.assertEqual(self.scene.health_pickups[0].amount, 10)

    def test_full_hp_player_never_receives_a_health_drop(self):
        self.scene.random_source = StubRandom(coin=1, roll=0.0)

        self._defeat_one_enemy()

        self.assertEqual(self.scene.health_pickups, [])

    def test_no_health_drop_when_two_are_already_on_the_map(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        self.scene.health_pickups = [
            HealthPickup(0.0, 0.0),
            HealthPickup(10.0, 10.0),
        ]

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 2)

    def test_collected_health_items_no_longer_count_toward_the_limit(self):
        self.scene.player.hp = 50
        self.scene.random_source = StubRandom(coin=1, roll=0.0)
        self.scene.health_pickups = [
            HealthPickup(0.0, 0.0),
            HealthPickup(10.0, 10.0),
        ]
        self.scene.health_pickups.pop()

        self._defeat_one_enemy()

        self.assertEqual(len(self.scene.health_pickups), 2)

    def test_walking_over_health_restores_ten_hp(self):
        self.scene.player.hp = 50
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups()

        self.assertEqual(self.scene.player.hp, 60)
        self.assertEqual(self.scene.health_pickups, [])

    def test_health_pickup_respects_the_max_hp(self):
        self.scene.player.hp = 95
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups()

        self.assertEqual(self.scene.player.hp, self.scene.player.max_hp)
        self.assertEqual(self.scene.health_pickups, [])

    def test_full_hp_player_leaves_the_health_pickup_on_the_map(self):
        self.scene.health_pickups.append(
            HealthPickup(self.scene.player.x, self.scene.player.y)
        )

        self.scene._update_pickups()

        self.assertEqual(len(self.scene.health_pickups), 1)


class BattleSceneFlowTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_q_pauses_the_battle_and_freezes_updates(self):
        self.scene.key_down("q")

        self.scene.update(0.1)

        self.assertTrue(self.scene.paused)
        self.assertEqual(self.scene.spawn_warnings, [])
        self.assertEqual(self.scene.gun.temperature, self.scene.gun.temperature)

    def test_q_resumes_the_battle(self):
        self.scene.key_down("q")
        self.scene.key_up("q")

        self.scene.key_down("q")

        self.assertFalse(self.scene.paused)

    def test_gameplay_keys_are_ignored_while_paused(self):
        original_mode = self.scene.gun.fire_mode
        self.scene.key_down("q")

        self.scene.key_down("e")

        self.assertEqual(self.scene.gun.fire_mode, original_mode)

    def test_pause_menu_navigation_wraps_around(self):
        self.scene.key_down("q")

        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 1)
        self.scene.key_up("s")
        self.scene.key_down("s")
        self.assertEqual(self.scene.pause_menu_index, 0)
        self.scene.key_up("s")
        self.scene.key_down("w")
        self.assertEqual(self.scene.pause_menu_index, 1)

    def test_resume_option_closes_the_pause_menu(self):
        self.scene.key_down("q")

        self.scene.key_down("return")

        self.assertFalse(self.scene.paused)
        self.assertFalse(self.scene.finished)

    def test_quit_option_finishes_the_battle(self):
        self.scene.key_down("q")
        self.scene.key_down("s")
        self.scene.key_up("s")

        self.scene.key_down("return")

        self.assertTrue(self.scene.finished)
        self.assertFalse(self.scene.paused)
        self.assertIs(self.scene.result, BattleResult.QUIT)
        self.assertFalse(self.scene.exit_requested)

    def test_player_death_finishes_the_battle_as_a_defeat(self):
        self.scene.player.hp = 0

        self.scene.update(0.0)

        self.assertTrue(self.scene.finished)
        self.assertIs(self.scene.result, BattleResult.DEFEAT)

    def test_clearing_all_waves_finishes_the_battle_as_a_victory(self):
        self.scene.waves_cleared = True

        self.scene.update(0.0)

        self.assertTrue(self.scene.finished)
        self.assertIs(self.scene.result, BattleResult.VICTORY)

    def test_finished_battle_ignores_further_updates(self):
        self.scene.waves_cleared = True
        self.scene.update(0.0)
        warnings = list(self.scene.spawn_warnings)

        self.scene.update(1.0)

        self.assertEqual(self.scene.spawn_warnings, warnings)

    def test_enter_after_the_result_requests_leaving(self):
        self.scene.waves_cleared = True
        self.scene.update(0.0)

        self.scene.key_down("return")

        self.assertTrue(self.scene.exit_requested)

    def test_reset_map_clears_pause_and_result_state(self):
        self.scene.paused = True
        self.scene.finished = True
        self.scene.result = BattleResult.QUIT
        self.scene.exit_requested = True

        self.scene.reset_map()

        self.assertFalse(self.scene.paused)
        self.assertFalse(self.scene.finished)
        self.assertIsNone(self.scene.result)
        self.assertFalse(self.scene.exit_requested)


class BattleSceneDebugTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_debug_mode_enables_infinite_ammo_and_disables_heat(self):
        gun = self.scene.gun
        temperature = gun.temperature

        self.scene.key_down("f1")

        self.assertTrue(self.scene.debug_mode)
        self.assertTrue(gun.infinite_ammo)
        self.assertFalse(gun.heat_enabled)
        self.assertTrue(gun.try_fire())
        self.assertEqual(gun.temperature, temperature)

    def test_leaving_debug_mode_restores_heat(self):
        self.scene.key_down("f1")
        self.scene.key_up("f1")

        self.scene.key_down("f1")

        self.assertFalse(self.scene.debug_mode)
        self.assertFalse(self.scene.gun.infinite_ammo)
        self.assertTrue(self.scene.gun.heat_enabled)

    def test_reset_map_keeps_heat_disabled_in_debug_mode(self):
        self.scene.key_down("f1")

        self.scene.reset_map()

        self.assertTrue(self.scene.debug_mode)
        self.assertTrue(self.scene.gun.infinite_ammo)
        self.assertFalse(self.scene.gun.heat_enabled)


class BattleSceneRecordTests(unittest.TestCase):
    def setUp(self):
        self.scene = make_scene(total_waves=1, spawn_rate=1000)

    def tearDown(self):
        game_world.clear()

    def test_elapsed_time_accumulates_while_active(self):
        self.scene.update(0.1)

        self.scene.update(0.2)

        self.assertAlmostEqual(self.scene.elapsed_time, 0.3)

    def test_pausing_stops_the_clock(self):
        self.scene.update(0.1)

        self.scene.key_down("q")
        self.scene.update(5.0)

        self.assertAlmostEqual(self.scene.elapsed_time, 0.1)

    def test_victory_records_the_clear_time(self):
        self.scene.waves_cleared = True

        self.scene.update(0.25)

        self.assertIs(self.scene.result, BattleResult.VICTORY)
        self.assertAlmostEqual(self.scene.clear_time, 0.25)

    def test_defeat_does_not_record_a_clear_time(self):
        self.scene.update(0.1)
        self.scene.player.hp = 0

        self.scene.update(0.2)

        self.assertIs(self.scene.result, BattleResult.DEFEAT)
        self.assertIsNone(self.scene.clear_time)
        self.assertAlmostEqual(self.scene.elapsed_time, 0.3)

    def test_quitting_keeps_the_reached_wave(self):
        self.scene.reached_wave = 4

        self.scene.key_down("q")
        self.scene.key_down("s")
        self.scene.key_up("s")
        self.scene.key_down("return")

        self.assertIs(self.scene.result, BattleResult.QUIT)
        self.assertEqual(self.scene.reached_wave, 4)
        self.assertIsNone(self.scene.clear_time)

    def test_reset_map_clears_record_values(self):
        self.scene.elapsed_time = 30.0
        self.scene.reached_wave = 9
        self.scene.clear_time = 30.0

        self.scene.reset_map()

        self.assertEqual(self.scene.elapsed_time, 0.0)
        self.assertEqual(self.scene.reached_wave, 1)
        self.assertIsNone(self.scene.clear_time)

    def test_development_settings_configure_the_wave_director(self):
        scene = BattleScene(
            Player(WORLD_WIDTH / 2, WORLD_HEIGHT / 2),
            Gun(),
            FakeBackground(),
            hud_font=FakeFont(),
            enemy_images={enemy_type: FakeImage() for enemy_type in EnemyType},
            enemy_draw_rectangle=lambda *args: None,
            enemy_draw_circle=lambda *args: None,
            random_source=random.Random(0),
            total_waves=2,
            wave_spawn_rate=500,
        )

        self.assertEqual(scene.wave_director.total_waves, 2)
        self.assertEqual(scene.wave_director.spawn_rate, 500)

        scene.reset_map()

        self.assertEqual(scene.wave_director.total_waves, 2)
        self.assertEqual(scene.wave_director.spawn_rate, 500)


if __name__ == "__main__":
    unittest.main()
