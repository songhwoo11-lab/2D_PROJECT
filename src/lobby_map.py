"""Static layout of the lobby: obstacles and interactive locations."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LobbyRect:
    """Axis aligned rectangle in lobby world coordinates."""

    left: float
    bottom: float
    right: float
    top: float

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.top - self.bottom

    @property
    def center_x(self):
        return (self.left + self.right) / 2

    @property
    def center_y(self):
        return (self.bottom + self.top) / 2


@dataclass(frozen=True)
class LobbyLocation:
    """A place in the lobby the player can walk up to and interact with."""

    key: str
    label: str
    zone_x: float
    zone_y: float
    zone_radius: float

    def contains(self, x, y):
        """Check whether the given position is inside the interaction area."""
        return math.hypot(x - self.zone_x, y - self.zone_y) <= self.zone_radius


# 장소 키와 그 장소에서 실행할 동작의 대응.
LOCATION_ACTIONS = {
    "shop": "enter_shop",
    "training": "enter_training",
    "records": "show_records",
}


# 로비에서 이용할 수 있는 장소와 그 상호작용 영역.
LOBBY_LOCATIONS = (    # 상점: 서쪽 시장 진열대 앞
    LobbyLocation(
        key="shop",
        label="SHOP",
        zone_x=600.0,
        zone_y=435.0,
        zone_radius=110.0,
    ),
    # 훈련장: 동쪽 표적과 무기 걸이대 앞
    LobbyLocation(
        key="training",
        label="TRAINING",
        zone_x=1500.0,
        zone_y=500.0,
        zone_radius=150.0,
    ),
    # 게임 시작 포털: 중앙 성벽 아치 앞
    LobbyLocation(
        key="portal",
        label="BATTLE PORTAL",
        zone_x=900.0,
        zone_y=620.0,
        zone_radius=130.0,
    ),
    # 기록 확인 지점: 포털 왼쪽 기록 보관 천막 앞
    LobbyLocation(
        key="records",
        label="RECORDS",
        zone_x=330.0,
        zone_y=435.0,
        zone_radius=110.0,
    ),
)
LOBBY_WALLS = (
    # 서쪽 시장 천막과 진열대
    LobbyRect(68, 500, 696, 830),
    # 남서쪽 기록 보관 천막
    LobbyRect(128, 216, 530, 372),
    # 전투 포털이 자리한 성벽 아치
    LobbyRect(767, 700, 1036, 1060),
    # 훈련장 무기 걸이대와 상자
    LobbyRect(1204, 540, 1458, 692),
    # 훈련장 표적 받침대
    LobbyRect(1472, 580, 1656, 692),
    # 훈련장 나무통
    LobbyRect(1687, 512, 1734, 583),
    # 훈련장 오른쪽 작업대
    LobbyRect(1649, 348, 1726, 489),
)
