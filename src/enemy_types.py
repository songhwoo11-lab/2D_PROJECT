"""Enemy archetypes backed by shared enemy behavior and stat data."""

from enemy import ENEMY_STATS, Enemy, EnemyType


class BasicEnemy(Enemy):
    def __init__(self, x, y, image=None, player=None, draw_rectangle=None):
        super().__init__(
            x,
            y,
            ENEMY_STATS[EnemyType.BASIC],
            image=image,
            player=player,
            draw_rectangle=draw_rectangle,
        )
