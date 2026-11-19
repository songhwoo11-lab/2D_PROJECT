from weapon import DEFAULT_GUN_ID, MACHINE_GUN_GUN_ID, RIFLE_GUN_ID


GUN_PRICES = {
    DEFAULT_GUN_ID: 0,
    RIFLE_GUN_ID: 100000,
    MACHINE_GUN_GUN_ID: 1000000,
}

GUN_SHOP_ORDER = (
    DEFAULT_GUN_ID,
    RIFLE_GUN_ID,
    MACHINE_GUN_GUN_ID,
)


def gun_price(gun_id):
    if gun_id not in GUN_PRICES:
        raise KeyError("unknown gun: {}".format(gun_id))
    return GUN_PRICES[gun_id]
