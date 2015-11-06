import json
import os

CURRENT_DIR = os.path.split(__file__)[0]

class GameMap(dict):

    def __init__(self):
        self.elegible_hqs = set()

    @classmethod
    def create_empty_map(cls, width, height):
        obj = cls()
        for x in xrange(0, width):
            for y in xrange(0, height):
                obj[x, y] = False
        obj.elegible_hqs = set([(0, 0), (0, height), (width, 0), (width, height)])

        return obj

    @property
    def width(self):
        return max(self.keys(), key=lambda e: e[0])[0]

    @property
    def height(self):
        return max(self.keys(), key=lambda e: e[1])[1]

    def iterrows(self):
        for y in xrange(0, self.height):
            yield (self[x, y] for x in xrange(0, self.width))


def iterate_over_layer(layer):
    width = layer['width']
    for idx, value in enumerate(layer['data']):
        y, x = divmod(idx, width)
        yield (x, y), value


def load_map(map_name):
    with open(os.path.join(CURRENT_DIR, 'maps', map_name)) as fh:
        data = json.load(fh)
        output = GameMap()
        for layer in data.get('layers'):
            name = layer['name'].lower()
            if name in ('water layer', 'blocking layer'):
                for coords, value in iterate_over_layer(layer):
                    current = output.setdefault(coords, True)
                    output[coords] = current and value

            elif name == 'hq layer':
                for coords, value in iterate_over_layer(layer):
                    if value:
                        output.elegible_hqs.add(coords)

        return output


if __name__ == '__main__':
    game_map = load_map('map_draft.json')
    for row in game_map.iterrows():
        print ''.join(' ' if cell else 'B' for cell in row)

    print game_map.elegible_hqs
