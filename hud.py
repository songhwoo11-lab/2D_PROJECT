"""Small vector-font HUD that does not require external font assets."""

_GLYPHS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("010", "101", "111", "101", "101"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    " ": ("000", "000", "000", "000", "000"),
    ":": ("000", "010", "000", "010", "000"),
    "/": ("001", "001", "010", "100", "100"),
}


def draw_text(text, x, y, draw_rectangle, scale=2):
    cursor_x = x
    for character in text:
        try:
            glyph = _GLYPHS[character]
        except KeyError as error:
            raise ValueError("unsupported HUD character: {!r}".format(character)) from error
        for row, pixels in enumerate(glyph):
            for column, pixel in enumerate(pixels):
                if pixel == "1":
                    left = cursor_x + column * scale
                    bottom = y + (4 - row) * scale
                    draw_rectangle(left, bottom, left + scale, bottom + scale)
        cursor_x += 4 * scale
    return cursor_x - x


def draw_hud(player, gun, result_text, draw_rectangle, set_color):
    bar_left = 20
    bar_bottom = 570
    bar_width = 200
    bar_height = 10
    hp_ratio = min(max(player.hp / player.max_hp, 0.0), 1.0)

    set_color(55, 45, 45)
    draw_rectangle(bar_left, bar_bottom, bar_left + bar_width, bar_bottom + bar_height)
    if hp_ratio:
        set_color(220, 45, 45)
        draw_rectangle(
            bar_left,
            bar_bottom,
            bar_left + bar_width * hp_ratio,
            bar_bottom + bar_height,
        )

    set_color(255, 255, 255)
    draw_text("HP {}/{}".format(player.hp, player.max_hp), 20, 550, draw_rectangle)
    draw_text("MODE: {}".format(gun.fire_mode.value.upper()), 20, 530, draw_rectangle)
    draw_text(
        "AMMO {}/{}".format(gun.magazine_ammo, gun.reserve_ammo),
        20,
        510,
        draw_rectangle,
    )
    if gun.reloading:
        draw_text("RELOAD", 20, 490, draw_rectangle)
    if result_text:
        draw_text(result_text, 20, 470, draw_rectangle)
