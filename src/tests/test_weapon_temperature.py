import unittest

from game_config import (
    COOLING_ACCELERATION_SCALE_SECONDS,
    COOLING_PER_SECOND_BLOCKED,
    COOLING_PER_SECOND_FIREABLE,
    FRAME_TIME,
    MIN_TEMPERATURE,
    OVERHEAT_REDUCTION_HOLD_SECONDS,
    OVERHEAT_REDUCTION_RECOVERY_SECONDS,
    PISTOL_TEMPERATURE_LIMIT,
)
from weapon import FireMode, Gun


class GunTemperatureStateTests(unittest.TestCase):
    def test_new_gun_starts_at_minimum_temperature_and_can_fire(self):
        gun = Gun()

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertEqual(gun.temperature_limit, PISTOL_TEMPERATURE_LIMIT)
        self.assertFalse(gun.fire_blocked)
        self.assertTrue(gun.can_fire)

    def test_overheated_gun_is_blocked_from_firing(self):
        gun = Gun()
        gun.overheated = True

        self.assertTrue(gun.fire_blocked)
        self.assertFalse(gun.can_fire)

    def test_reset_restores_temperature_and_clears_overheat(self):
        gun = Gun()
        gun.temperature = 123.0
        gun.overheated = True

        gun.reset()

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertFalse(gun.fire_blocked)
        self.assertTrue(gun.can_fire)


class SingleShotHeatTests(unittest.TestCase):
    def _ready_gun(self):
        gun = Gun()
        gun.infinite_ammo = True
        return gun

    def test_consecutive_single_shots_increase_heat_progressively(self):
        gun = self._ready_gun()

        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)
        self.assertEqual(gun.auto_shot_streak, 1)
        gun.cooldown_remaining = 0.0
        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.1)
        self.assertEqual(gun.auto_shot_streak, 2)
        gun.cooldown_remaining = 0.0
        self.assertTrue(gun.try_fire())
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.8)
        self.assertEqual(gun.auto_shot_streak, 3)

    def test_single_shot_heat_matches_auto_shot_heat(self):
        single_gun = self._ready_gun()
        auto_gun = self._ready_gun()
        auto_gun.fire_mode = FireMode.AUTO

        for _ in range(3):
            single_gun.try_fire()
            auto_gun.try_fire()
            single_gun.cooldown_remaining = 0.0
            auto_gun.cooldown_remaining = 0.0

        self.assertAlmostEqual(single_gun.temperature, auto_gun.temperature)
        self.assertEqual(
            single_gun.auto_shot_streak,
            auto_gun.auto_shot_streak,
        )

    def test_blocked_shot_does_not_add_heat(self):
        gun = self._ready_gun()
        gun.overheated = True
        gun.temperature = 42.0

        self.assertFalse(gun.try_fire())
        self.assertEqual(gun.temperature, 42.0)

    def test_temperature_is_clamped_to_limit(self):
        gun = self._ready_gun()
        gun.temperature = gun.temperature_limit - 0.2

        gun.try_fire()

        self.assertEqual(gun.temperature, gun.temperature_limit)


class AutoShotHeatTests(unittest.TestCase):
    def _auto_gun(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.fire_mode = FireMode.AUTO
        return gun

    def test_consecutive_auto_shots_increase_heat_progressively(self):
        gun = self._auto_gun()

        gun.try_fire()
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)
        self.assertEqual(gun.auto_shot_streak, 1)
        gun.cooldown_remaining = 0.0
        gun.try_fire()
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.1)
        self.assertEqual(gun.auto_shot_streak, 2)
        gun.cooldown_remaining = 0.0
        gun.try_fire()
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.8)
        self.assertEqual(gun.auto_shot_streak, 3)

    def test_streak_decays_once_per_full_idle_second(self):
        gun = self._auto_gun()
        for _ in range(3):
            gun.try_fire()
            gun.cooldown_remaining = 0.0
        self.assertEqual(gun.auto_shot_streak, 3)

        gun.update(1.0)
        self.assertEqual(gun.auto_shot_streak, 2)
        gun.update(0.5)
        self.assertEqual(gun.auto_shot_streak, 2)
        gun.update(0.5)
        self.assertEqual(gun.auto_shot_streak, 1)

    def test_streak_never_goes_below_zero(self):
        gun = self._auto_gun()
        gun.try_fire()

        gun.update(100.0)

        self.assertEqual(gun.auto_shot_streak, 0)


class FireModeHeatPersistenceTests(unittest.TestCase):
    def _ready_gun(self):
        gun = Gun()
        gun.infinite_ammo = True
        return gun

    def test_switching_to_auto_keeps_the_heat_increase(self):
        gun = self._ready_gun()
        gun.try_fire()
        gun.cooldown_remaining = 0.0

        gun.toggle_mode()
        gun.try_fire()

        self.assertEqual(gun.auto_shot_streak, 2)
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.1)

    def test_switching_to_single_keeps_the_heat_increase(self):
        gun = self._ready_gun()
        gun.fire_mode = FireMode.AUTO
        gun.try_fire()
        gun.cooldown_remaining = 0.0
        gun.try_fire()
        gun.cooldown_remaining = 0.0

        gun.toggle_mode()
        gun.try_fire()

        self.assertEqual(gun.auto_shot_streak, 3)
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 1.8)

    def test_repeated_mode_switching_does_not_reset_the_streak(self):
        gun = self._ready_gun()
        gun.try_fire()
        gun.cooldown_remaining = 0.0
        gun.try_fire()
        gun.cooldown_remaining = 0.0

        gun.toggle_mode()
        gun.toggle_mode()
        gun.toggle_mode()

        self.assertEqual(gun.auto_shot_streak, 2)


class DebugHeatTests(unittest.TestCase):
    def test_new_gun_has_heat_enabled(self):
        self.assertTrue(Gun().heat_enabled)

    def test_disabled_heat_keeps_single_shot_temperature(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.heat_enabled = False

        self.assertTrue(gun.try_fire())

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)

    def test_disabled_heat_keeps_auto_shot_temperature(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.fire_mode = FireMode.AUTO
        gun.heat_enabled = False

        for _ in range(5):
            self.assertTrue(gun.try_fire())
            gun.cooldown_remaining = 0.0

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)

    def test_reenabling_heat_restores_temperature_gain(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.heat_enabled = False
        gun.try_fire()
        gun.cooldown_remaining = 0.0

        gun.heat_enabled = True
        self.assertTrue(gun.try_fire())

        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)

    def test_reset_reenables_heat(self):
        gun = Gun()
        gun.heat_enabled = False

        gun.reset()

        self.assertTrue(gun.heat_enabled)


class FireableCoolingTests(unittest.TestCase):
    def test_temperature_drops_at_the_base_rate_right_after_a_shot(self):
        gun = Gun()
        gun.temperature = 100.0

        gun.update(FRAME_TIME)

        self.assertAlmostEqual(gun.temperature, 99.95, places=5)

    def test_cooling_accumulates_over_frames(self):
        gun = Gun()
        gun.temperature = 100.0

        for _ in range(20):
            gun.update(FRAME_TIME)

        self.assertAlmostEqual(gun.temperature, 98.998406, places=5)

    def test_cooling_does_not_go_below_minimum(self):
        gun = Gun()
        gun.temperature = MIN_TEMPERATURE + 0.01

        gun.update(FRAME_TIME)

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)


class CoolingAccelerationTests(unittest.TestCase):
    def test_cooling_rate_starts_at_the_base_rate(self):
        gun = Gun()

        self.assertAlmostEqual(
            gun.cooling_rate,
            COOLING_PER_SECOND_FIREABLE,
        )

    def test_cooling_rate_grows_quadratically_while_idle(self):
        gun = Gun()
        gun.update(COOLING_ACCELERATION_SCALE_SECONDS)

        self.assertAlmostEqual(
            gun.cooling_rate,
            COOLING_PER_SECOND_FIREABLE * 2.0,
        )
        gun.update(COOLING_ACCELERATION_SCALE_SECONDS)
        self.assertAlmostEqual(
            gun.cooling_rate,
            COOLING_PER_SECOND_FIREABLE * 5.0,
        )

    def test_idle_cooling_speeds_up_over_time(self):
        gun = Gun()
        gun.temperature = 100.0

        gun.update(1.0)
        first_drop = 100.0 - gun.temperature
        gun.temperature = 100.0
        gun.update(1.0)
        second_drop = 100.0 - gun.temperature

        self.assertGreater(second_drop, first_drop)

    def test_firing_resets_the_cooling_acceleration(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.update(10.0)
        accelerated_rate = gun.cooling_rate

        gun.try_fire()

        self.assertGreater(accelerated_rate, COOLING_PER_SECOND_FIREABLE)
        self.assertAlmostEqual(gun.cooling_rate, COOLING_PER_SECOND_FIREABLE)

    def test_firing_raises_the_temperature_again_before_cooling_resets(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.temperature = 60.0
        gun.update(10.0)
        temperature_before_shot = gun.temperature

        gun.try_fire()

        self.assertGreater(gun.temperature, temperature_before_shot)
        self.assertAlmostEqual(gun.cooling_rate, COOLING_PER_SECOND_FIREABLE)

    def test_blocked_cooling_rate_is_not_accelerated(self):
        gun = Gun()
        gun.overheated = True
        gun.temperature = 100.0
        gun.update(1.0)

        self.assertAlmostEqual(
            gun.temperature,
            100.0 - COOLING_PER_SECOND_BLOCKED * 1.0,
        )

    def test_reset_clears_the_cooling_acceleration(self):
        gun = Gun()
        gun.update(10.0)

        gun.reset()

        self.assertAlmostEqual(gun.cooling_rate, COOLING_PER_SECOND_FIREABLE)


class OverheatTests(unittest.TestCase):
    def test_reaching_limit_blocks_firing(self):
        gun = Gun()
        gun.infinite_ammo = True
        gun.temperature = gun.temperature_limit - 0.1

        self.assertTrue(gun.try_fire())

        self.assertEqual(gun.temperature, gun.temperature_limit)
        self.assertTrue(gun.overheated)
        self.assertTrue(gun.fire_blocked)
        self.assertFalse(gun.can_fire)
        gun.cooldown_remaining = 0.0
        self.assertFalse(gun.try_fire())

    def test_blocked_gun_cools_half_degree_per_frame(self):
        gun = Gun()
        gun.overheated = True
        gun.temperature = gun.temperature_limit

        gun.update(FRAME_TIME)

        self.assertAlmostEqual(
            gun.temperature,
            gun.temperature_limit - 0.5,
        )

    def test_gun_becomes_fireable_again_at_minimum_temperature(self):
        gun = Gun()
        gun.overheated = True
        gun.temperature = MIN_TEMPERATURE + 0.5

        gun.update(FRAME_TIME)

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertFalse(gun.overheated)
        self.assertTrue(gun.can_fire)

    def test_full_recovery_from_limit_takes_380_frames(self):
        gun = Gun()
        gun.overheated = True
        gun.temperature = gun.temperature_limit

        for _ in range(380):
            gun.update(FRAME_TIME)

        self.assertEqual(gun.temperature, MIN_TEMPERATURE)
        self.assertFalse(gun.overheated)


class OverheatAutoStreakResetTests(unittest.TestCase):
    def _overheated_auto_gun(self, streak):
        gun = Gun()
        gun.infinite_ammo = True
        gun.fire_mode = FireMode.AUTO
        for _ in range(streak):
            gun.try_fire()
            gun.cooldown_remaining = 0.0
        gun.temperature = gun.temperature_limit
        gun.overheated = True
        return gun

    def test_streak_is_kept_while_the_gun_is_still_cooling(self):
        gun = self._overheated_auto_gun(3)
        gun.temperature = MIN_TEMPERATURE + 1.0

        gun.update(FRAME_TIME)

        self.assertEqual(gun.auto_shot_streak, 3)
        self.assertTrue(gun.overheated)
        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)

    def test_streak_is_reset_when_the_gun_becomes_fireable_again(self):
        gun = self._overheated_auto_gun(3)
        gun.temperature = MIN_TEMPERATURE + 0.5

        gun.update(FRAME_TIME)

        self.assertFalse(gun.overheated)
        self.assertTrue(gun.can_fire)
        self.assertEqual(gun.auto_shot_streak, 0)

    def test_heat_per_shot_returns_to_the_base_amount_after_recovery(self):
        gun = self._overheated_auto_gun(3)
        gun.temperature = MIN_TEMPERATURE + 0.5
        gun.update(FRAME_TIME)
        gun.temperature = MIN_TEMPERATURE

        gun.cooldown_remaining = 0.0
        gun.try_fire()

        self.assertAlmostEqual(gun.temperature, MIN_TEMPERATURE + 0.5)
        self.assertEqual(gun.auto_shot_streak, 1)

    def test_streak_is_reset_after_a_full_recovery_from_the_limit(self):
        gun = self._overheated_auto_gun(5)

        for _ in range(380):
            gun.update(FRAME_TIME)

        self.assertFalse(gun.overheated)
        self.assertEqual(gun.auto_shot_streak, 0)


class OverheatDamageReductionTests(unittest.TestCase):
    def _recovered_gun(self):
        gun = Gun()
        gun.overheated = True
        gun.temperature = MIN_TEMPERATURE + 0.5
        gun.update(FRAME_TIME)
        return gun

    def test_gun_without_overheat_has_full_damage(self):
        gun = Gun()

        self.assertEqual(gun.damage_reduction, 0.0)
        self.assertAlmostEqual(gun.damage_multiplier, 1.0)
        self.assertAlmostEqual(gun.effective_damage, gun.spec.damage)

    def test_recovery_starts_with_80_percent_reduction(self):
        gun = self._recovered_gun()

        self.assertAlmostEqual(gun.damage_reduction, 0.8)
        self.assertAlmostEqual(gun.damage_multiplier, 0.2)
        self.assertAlmostEqual(gun.effective_damage, gun.spec.damage * 0.2)

    def test_reduction_is_held_for_ten_seconds(self):
        gun = self._recovered_gun()

        gun.update(9.0)

        self.assertAlmostEqual(gun.damage_reduction, 0.8)

    def test_reduction_follows_an_exponential_curve_after_the_hold(self):
        gun = self._recovered_gun()

        gun.update(45.0)

        self.assertAlmostEqual(gun.damage_reduction, 0.459854, places=6)
        self.assertAlmostEqual(gun.damage_multiplier, 0.540146, places=6)

    def test_reduction_decreases_slowly_then_steeply(self):
        gun = self._recovered_gun()

        gun.update(35.0)
        halfway_reduction = gun.damage_reduction
        gun.update(25.0)

        self.assertAlmostEqual(gun.damage_reduction, 0.0)
        first_half_drop = 0.8 - halfway_reduction
        second_half_drop = halfway_reduction
        self.assertGreater(second_half_drop, first_half_drop)

    def test_reduction_is_gone_after_sixty_seconds(self):
        gun = self._recovered_gun()

        gun.update(60.0)

        self.assertAlmostEqual(gun.damage_reduction, 0.0)
        self.assertAlmostEqual(gun.damage_multiplier, 1.0)

    def test_reset_clears_damage_reduction(self):
        gun = self._recovered_gun()

        gun.reset()

        self.assertAlmostEqual(gun.damage_multiplier, 1.0)

    def test_remaining_reduction_time_is_zero_without_overheat(self):
        gun = Gun()

        self.assertEqual(gun.damage_reduction_remaining, 0.0)

    def test_hold_time_starts_at_thirty_seconds(self):
        gun = self._recovered_gun()

        self.assertAlmostEqual(
            gun.damage_reduction_remaining,
            OVERHEAT_REDUCTION_HOLD_SECONDS,
        )

    def test_hold_time_counts_down(self):
        gun = self._recovered_gun()

        gun.update(5.0)

        self.assertAlmostEqual(gun.damage_reduction_remaining, 5.0)

    def test_recovery_time_starts_at_fifty_seconds(self):
        gun = self._recovered_gun()

        gun.update(OVERHEAT_REDUCTION_HOLD_SECONDS)

        self.assertAlmostEqual(
            gun.damage_reduction_remaining,
            OVERHEAT_REDUCTION_RECOVERY_SECONDS,
        )

    def test_recovery_time_counts_down(self):
        gun = self._recovered_gun()

        gun.update(35.0)

        self.assertAlmostEqual(gun.damage_reduction_remaining, 25.0)

    def test_remaining_reduction_time_reaches_zero(self):
        gun = self._recovered_gun()

        gun.update(
            OVERHEAT_REDUCTION_HOLD_SECONDS
            + OVERHEAT_REDUCTION_RECOVERY_SECONDS
        )

        self.assertEqual(gun.damage_reduction_remaining, 0.0)


if __name__ == "__main__":
    unittest.main()
