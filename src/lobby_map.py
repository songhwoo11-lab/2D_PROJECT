"""Static layout of the lobby: obstacles and interactive locations."""

from dataclasses import dataclass


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


# 로비 배경의 배치물에 대응하는 통행 불가 영역.
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
