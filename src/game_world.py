"""Layered storage and lifecycle helpers for game objects."""

import math

from game_config import UI_SCALE

world = [[], []]
_SPATIAL_CELL_SIZE = 64.0 * UI_SCALE
_spatial_cells = None
_spatial_positions = None
_spatial_max_radius = 0.0


def _spatial_cell(x, y):
    return (
        math.floor(x / _SPATIAL_CELL_SIZE),
        math.floor(y / _SPATIAL_CELL_SIZE),
    )


def _add_to_spatial_index(obj):
    cell = _spatial_cell(obj.x, obj.y)
    _spatial_cells.setdefault(cell, set()).add(obj)
    _spatial_positions[obj] = cell


def _build_spatial_index():
    global _spatial_cells, _spatial_positions, _spatial_max_radius
    _spatial_cells = {}
    _spatial_positions = {}
    _spatial_max_radius = 0.0
    for layer in world:
        for obj in layer:
            if getattr(obj, "_uses_spatial_collision", False) and obj.is_alive:
                _add_to_spatial_index(obj)
                _spatial_max_radius = max(_spatial_max_radius, obj.radius)


def nearby_spatial_objects(obj, search_radius):
    if _spatial_cells is None:
        candidates = (
            candidate
            for layer in world
            for candidate in layer
            if candidate is not obj
            and getattr(candidate, "_uses_spatial_collision", False)
            and candidate.is_alive
        )
    else:
        expanded_radius = search_radius + _spatial_max_radius
        min_x, min_y = _spatial_cell(obj.x - expanded_radius, obj.y - expanded_radius)
        max_x, max_y = _spatial_cell(obj.x + expanded_radius, obj.y + expanded_radius)
        candidates = (
            candidate
            for cell_x in range(min_x, max_x + 1)
            for cell_y in range(min_y, max_y + 1)
            for candidate in _spatial_cells.get((cell_x, cell_y), ())
            if candidate is not obj and candidate.is_alive
        )
    return [
        candidate
        for candidate in candidates
        if math.hypot(candidate.x - obj.x, candidate.y - obj.y)
        <= search_radius + candidate.radius
    ]


def refresh_spatial_position(obj):
    if _spatial_cells is None or obj not in _spatial_positions:
        return
    old_cell = _spatial_positions[obj]
    new_cell = _spatial_cell(obj.x, obj.y)
    if old_cell == new_cell:
        return
    _spatial_cells[old_cell].remove(obj)
    if not _spatial_cells[old_cell]:
        del _spatial_cells[old_cell]
    _spatial_cells.setdefault(new_cell, set()).add(obj)
    _spatial_positions[obj] = new_cell


def add_object(obj, depth=0):
    if depth < 0:
        raise ValueError("depth must be non-negative")
    while depth >= len(world):
        world.append([])
    world[depth].append(obj)


def remove_object(obj):
    for layer in world:
        if obj in layer:
            layer.remove(obj)
            return


def update():
    _build_spatial_index()
    try:
        for layer in tuple(world):
            for obj in tuple(layer):
                if obj in layer:
                    obj.update()
    finally:
        _clear_spatial_index()


def _clear_spatial_index():
    global _spatial_cells, _spatial_positions, _spatial_max_radius
    _spatial_cells = None
    _spatial_positions = None
    _spatial_max_radius = 0.0


def render(should_render=None):
    for layer in tuple(world):
        for obj in tuple(layer):
            if obj in layer and (should_render is None or should_render(obj)):
                obj.draw()


def clear():
    for layer in world:
        layer.clear()
    _clear_spatial_index()