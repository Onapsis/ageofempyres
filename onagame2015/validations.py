
def coord_in_arena(coord, arena):
    """
    :coord: namedtuple representing a coordinate with the properties coord.latitude
    and coord.longitude
    :arena: Arena object that has arena.{width,height}
    @return: <bool> indicating if the unit is inside the arena.
    """
    return (0 <= coord.latitude < arena.width and 0 <= coord.longitude < arena.height)
