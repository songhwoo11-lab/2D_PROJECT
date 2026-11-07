"""Player state and rendering for the first playable battle stage."""

from game_config import PLAYER_MAX_HP, PLAYER_RADIUS, PLAYER_SPEED


class Player:
    def __init__(
        self,
        x,
        y,
        image=None,
        max_hp=PLAYER_MAX_HP,
        speed=PLAYER_SPEED,
        radius=PLAYER_RADIUS,
    ):
        self.x = float(x)
        self.y = float(y)
        self.image = image
        self.max_hp = int(max_hp)
        self.hp = self.max_hp
        self.speed = float(speed)
        self.radius = float(radius)
        self.aim_angle = 0.0
        self._move_x = 0.0
        self._move_y = 0.0
        self._delta_time = 0.0

    def update(self):
        pass

    def draw(self, screen_x=None, screen_y=None):
        if self.image is None:
            raise RuntimeError("Player.draw requires a loaded player image")
        x = self.x if screen_x is None else screen_x
        y = self.y if screen_y is None else screen_y
        self.image.draw(x, y, self.radius * 2, self.radius * 2)
