"""World-to-screen camera conversion for the scrolling battle map."""

from game_config import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)


class Camera:
    def __init__(
        self,
        screen_width=SCREEN_WIDTH,
        screen_height=SCREEN_HEIGHT,
        world_width=WORLD_WIDTH,
        world_height=WORLD_HEIGHT,
    ):
        self.screen_width = float(screen_width)
        self.screen_height = float(screen_height)
        self.world_width = float(world_width)
        self.world_height = float(world_height)
        self.x = 0.0
        self.y = 0.0

    def follow(self, world_x, world_y):
        self.x = self._clamp_offset(
            world_x - self.screen_width / 2,
            self.world_width - self.screen_width,
        )
        self.y = self._clamp_offset(
            world_y - self.screen_height / 2,
            self.world_height - self.screen_height,
        )

    @staticmethod
    def _clamp_offset(offset, max_offset):
        return min(max(offset, 0.0), max(max_offset, 0.0))

    def world_to_screen(self, world_x, world_y):
        return world_x - self.x, world_y - self.y

    def screen_to_world(self, screen_x, screen_y, origin_top=False):
        if origin_top:
            screen_y = self.screen_height - screen_y
        return screen_x + self.x, screen_y + self.y
