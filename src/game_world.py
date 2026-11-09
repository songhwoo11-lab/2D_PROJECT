"""Layered storage and lifecycle helpers for game objects."""

world = [[], []]


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
    for layer in tuple(world):
        for obj in tuple(layer):
            if obj in layer:
                obj.update()


def render():
    for layer in tuple(world):
        for obj in tuple(layer):
            if obj in layer:
                obj.draw()


def clear():
    for layer in world:
        layer.clear()