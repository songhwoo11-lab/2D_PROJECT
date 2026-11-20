"""Progress that is kept for the whole game session."""

from battle_record import BattleRecord, TrainingRecord
from dev_settings import development_coins, development_gun
from weapon import WEAPON_SPECS


DEFAULT_OWNED_GUNS = ("pistol",)


class GameState:
    """Coins, owned guns, and battle records shared between the scenes."""

    def __init__(
        self,
        owned_guns=DEFAULT_OWNED_GUNS,
        coins=None,
        records=None,
        training_records=None,
        dev_gun=None,
        upgrade_levels=None,
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
        self.dev_gun = dev_gun if dev_gun is not None else development_gun()
        self.selected_gun = self.dev_gun or (
            self.owned_guns[0] if self.owned_guns else None
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
