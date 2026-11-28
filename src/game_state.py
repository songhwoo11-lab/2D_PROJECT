"""Progress that is kept for the whole game session."""

from battle_record import BattleRecord, TrainingRecord, VICTORY
from dev_settings import development_coins, development_gun
from game_config import DEFAULT_DIFFICULTY, TOTAL_WAVES, normalize_difficulty
from save_data import SaveData, limit_recent_logs, select_best_log
from shop import GUN_SHOP_ORDER
from weapon import WEAPON_SPECS


DEFAULT_OWNED_GUNS = ("pistol",)


def _record_from_log(wave, elapsed_time):
    is_victory = wave >= TOTAL_WAVES
    return BattleRecord(
        result=VICTORY if is_victory else "defeat",
        reached_wave=wave,
        elapsed_time=elapsed_time,
        clear_time=elapsed_time if is_victory else None,
    )


class GameState:
    """Coins, owned guns, and battle records shared between the scenes."""

    def __init__(
        self,
        owned_guns=DEFAULT_OWNED_GUNS,
        coins=None,
        records=None,
        training_records=None,
        best_log=None,
        dev_gun=None,
        upgrade_levels=None,
        difficulty=DEFAULT_DIFFICULTY,
    ):
        self.owned_guns = list(owned_guns)
        self.upgrade_levels = {
            gun_id: 0 for gun_id in WEAPON_SPECS
        }
        if upgrade_levels is not None:
            self.upgrade_levels.update(upgrade_levels)
        coin_override = development_coins() if coins is None else coins
        self.coins = 0 if coin_override is None else coin_override
        self.records = list(records or [])
        self.training_records = list(training_records or [])
        self.best_log = best_log
        self.dev_gun = dev_gun if dev_gun is not None else development_gun()
        self.selected_gun = self.dev_gun or (
            self.owned_guns[0] if self.owned_guns else None
        )
        self.difficulty = normalize_difficulty(difficulty)

    @classmethod
    def from_save_data(cls, data, dev_gun=None, coins=None):
        """Build the live game state from the loaded save data."""
        owned_guns = [
            gun_id
            for gun_id, owned in zip(GUN_SHOP_ORDER, data.acquired_guns)
            if owned
        ]
        upgrade_levels = {
            gun_id: level
            for gun_id, level in zip(GUN_SHOP_ORDER, data.upgrade_levels)
        }
        coin_override = development_coins() if coins is None else coins
        logs = list(data.recent_logs)
        if not logs and data.best_log is not None:
            logs.append((data.best_log.reached_wave, data.best_log.elapsed_time))
        records = [_record_from_log(wave, elapsed) for wave, elapsed in logs]
        training_records = [
            TrainingRecord(targets_destroyed=count)
            for count in data.training_records
        ]
        return cls(
            owned_guns=owned_guns,
            coins=data.coins if coin_override is None else coin_override,
            records=records,
            training_records=training_records,
            best_log=data.best_log,
            dev_gun=dev_gun if dev_gun is not None else development_gun(),
            upgrade_levels=upgrade_levels,
            difficulty=data.difficulty,
        )

    def to_save_data(self):
        """Convert the live state into the data written to game files."""
        all_logs = [
            (record.reached_wave, record.elapsed_time) for record in self.records
        ]
        recent_logs = limit_recent_logs(all_logs)
        best_candidates = list(all_logs)
        if self.best_log is not None:
            best_candidates.append(
                (self.best_log.reached_wave, self.best_log.elapsed_time)
            )
        best_log = select_best_log(best_candidates)
        return SaveData(
            acquired_guns=[gun_id in self.owned_guns for gun_id in GUN_SHOP_ORDER],
            upgrade_levels=[self.upgrade_level(gun_id) for gun_id in GUN_SHOP_ORDER],
            coins=self.coins,
            best_log=best_log,
            recent_logs=recent_logs,
            training_records=[
                record.targets_destroyed for record in self.training_records
            ],
            difficulty=self.difficulty,
        )

    def add_record(self, record):
        """Store the newest battle record in front of the older ones."""
        self.records.insert(0, record)

    def add_training_record(self, record):
        """Store the newest training record in front of the older ones."""
        self.training_records.insert(0, record)

    def owns_gun(self, gun_id):
        return gun_id in self.owned_guns

    def upgrade_level(self, gun_id):
        return self.upgrade_levels.get(gun_id, 0)

    def set_upgrade_level(self, gun_id, level):
        self.upgrade_levels[gun_id] = level
        return level

    def needs_gun_selection(self):
        """Check whether a gun selection screen is required before a battle."""
        return self.dev_gun is None and len(self.owned_guns) >= 1

    def select_gun(self, gun_id):
        if not self.owns_gun(gun_id):
            raise ValueError("gun is not owned: {}".format(gun_id))
        self.selected_gun = gun_id
        return self.selected_gun

    def set_difficulty(self, difficulty):
        """Remember the difficulty chosen for the next battle."""
        self.difficulty = normalize_difficulty(difficulty)
        return self.difficulty
