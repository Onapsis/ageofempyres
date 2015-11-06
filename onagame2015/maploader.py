import json
import os

CURRENT_DIR = os.path.split(__file__)[0]

class BlockerMap(dict):

    def __init__(self):
        self.elegible_hqs = set()

    @property
    def width(self):
        return max(self.keys(), key=lambda e: e[0])[0]

    @property
    def height(self):
        return max(self.keys(), key=lambda e: e[1])[1]

    def iterrows(self):
        for y in xrange(0, blockers.width):
            yield (self[x, y] for x in xrange(0, blockers.height))


def iterate_over_layer(layer):
    width = layer['width']
    for idx, value in enumerate(layer['data']):
        y, x = divmod(idx, width)
        yield (x, y), value


def load_map(map_name):
    with open(os.path.join(CURRENT_DIR, 'maps', map_name)) as fh:
        data = json.load(fh)
        output = BlockerMap()
        for layer in data.get('layers'):
            name = layer['name'].lower()
            if name in ('water layer', 'blocking layer'):
                for coords, value in iterate_over_layer(layer):
                    current = output.setdefault(coords, False)
                    output[coords] = current or value

            elif name == 'hq layer':
                for coords, value in iterate_over_layer(layer):
                    if value:
                        output.elegible_hqs.add(coords)

        return output


if __name__ == '__main__':


    blockers = load_map('map_draft.json')
    for row in blockers.iterrows():
        print ''.join('B' if block else ' ' for block in row)

    print blockers.elegible_hqs
