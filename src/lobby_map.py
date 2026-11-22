"""Static layout of the lobby: fixed locations and wasd transitions."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LobbyLocation:
    """A fixed location the lobby player can stand at."""

    key: str
    label: str
    zone_x: float
    zone_y: float
    zone_radius: float

    def contains(self, x, y):
        """Check whether the given position is inside the interaction area."""
        return math.hypot(x - self.zone_x, y - self.zone_y) <= self.zone_radius


LOBBY_START_KEY = "center"

# 장소 키와 그 장소에서 Enter로 실행할 동작의 대응.
LOCATION_ACTIONS = {
    "shop": "enter_shop",
    "training": "enter_training",
    "portal": "enter_portal",
    "records": "show_records",
    "stairs": "exit_game",
}

# 고정된 로비 위치. 중앙을 기준으로 wasd로 인접한 장소만 이동한다.
LOBBY_LOCATIONS = (
    LobbyLocation(
        key="shop",
        label="SHOP",
        zone_x=330.0,
        zone_y=435.0,
        zone_radius=110.0,
    ),
    LobbyLocation(
        key="records",
        label="RECORDS",
        zone_x=600.0,
        zone_y=435.0,
        zone_radius=110.0,
    ),
    LobbyLocation(
        key="center",
        label="CENTER",
        zone_x=900.0,
        zone_y=450.0,
        zone_radius=80.0,
    ),
    LobbyLocation(
        key="portal",
        label="BATTLE PORTAL",
        zone_x=900.0,
        zone_y=750.0,
        zone_radius=240.0,
    ),
    LobbyLocation(
        key="training",
        label="TRAINING",
        zone_x=1500.0,
        zone_y=500.0,
        zone_radius=150.0,
    ),
    LobbyLocation(
        key="stairs",
        label="EXIT GAME",
        zone_x=900.0,
        zone_y=120.0,
        zone_radius=80.0,
    ),
)

LOBBY_NODE_BY_KEY = {location.key: location for location in LOBBY_LOCATIONS}

LOBBY_MOVES = {
    ("shop", "d"): "records",
    ("records", "d"): "center",
    ("records", "a"): "shop",
    ("center", "a"): "records",
    ("center", "s"): "stairs",
    ("center", "d"): "training",
    ("center", "w"): "portal",
    ("training", "a"): "center",
    ("portal", "s"): "center",
    ("stairs", "w"): "center",
}
