
def coord_in_arena(coord, arena):
    """
    :coord: namedtuple representing a coordinate with the properties coord.x
    and coord.y
    :arena: Arena object that has arena.{width,height}
    @return: <bool> indicating if the unit is inside the arena.
    """
    return (0 <= coord.x < arena.height and 0 <= coord.y < arena.width)
