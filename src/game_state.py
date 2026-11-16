"""Progress that is kept for the whole game session."""

from battle_record import BattleRecord


DEFAULT_OWNED_GUNS = ("pistol",)


class GameState:
    """Coins, owned guns, and battle records shared between the scenes."""

    def __init__(self, owned_guns=DEFAULT_OWNED_GUNS, coins=0, records=None):
        self.owned_guns = list(owned_guns)
        self.coins = coins
        self.records = list(records or [])
        self.selected_gun = self.owned_guns[0] if self.owned_guns else None

    def add_record(self, record):
        """Store the newest battle record in front of the older ones."""
        self.records.insert(0, record)

    def owns_gun(self, gun_id):
        return gun_id in self.owned_guns

    def select_gun(self, gun_id):
        if not self.owns_gun(gun_id):
            raise ValueError("gun is not owned: {}".format(gun_id))
        self.selected_gun = gun_id
        return self.selected_gun
