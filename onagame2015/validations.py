from onagame2015.lib import AVAILABLE_MOVEMENTS


def coord_in_arena(coord, arena):
    """
    :coord: namedtuple representing a coordinate with the properties coord.latitude
    and coord.longitude
    :arena: Arena object that has arena.{width,height}
    @return: <bool> indicating if the unit is inside the arena.
    """
    return (0 <= coord.latitude < arena.width and 0 <= coord.longitude < arena.height)


def direction_is_valid(direction):
    try:
        return tuple(direction) in AVAILABLE_MOVEMENTS
    except TypeError:
        return False
