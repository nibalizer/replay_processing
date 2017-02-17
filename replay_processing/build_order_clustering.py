import argparse
import collections
import csv
import heapq
import sys

import numpy as np
from sklearn.preprocessing import scale
from sklearn.decomposition import PCA

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("build_order_csv",
                        help="Path to build order CSV.",
                        type=str)
    parser.add_argument("--time-cutoff",
                        help="Seconds to stop considering data.",
                        type=int,
                        default=0)

    return parser.parse_args(args)


Unit = collections.namedtuple('Unit', ['type', 'name'])


BuildItem = collections.namedtuple('BuildItem', ['time', 'unit'])


class PlayerBuild(object):
    def __init__(self):
        self._items = []

    @property
    def items(self):
        return sorted(self._items)

    @property
    def units(self):
        return set([x.unit for x in self._items])

    def add_build_item(self, item):
        heapq.heappush(self._items, item)

    def common_units(self, other_build):
        return self.units & other_build.units


def main():
    args = parse_args(sys.argv[1:])

    player_builds = collections.defaultdict(PlayerBuild)

    player_id_map = {}
    player_map = {}

    with open(args.build_order_csv, newline='') as infile:
        csvfile = csv.reader(infile, delimiter=',', quotechar='|')
        next(csvfile)
        for row in csvfile:
            ev_time = int(row[0])
            if ev_time > 0 and (args.time_cutoff == 0 or ev_time <= int(args.time_cutoff)):
                player = row[1]
                try:
                    player_id = player_id_map[player]
                except KeyError:
                    player_id = len(player_id_map)
                    player_id_map[player] = player_id
                    player_map[player_id] = player

                unit = Unit(row[2], row[3])
                build_item = BuildItem(row[0], unit)
                player_builds[player_id].add_build_item(build_item)

    dist_matrix = np.empty(shape=(len(player_builds), len(player_builds)))
    for player, build in player_builds.items():
        for other_player, other_build in player_builds.items():
            dist_matrix.itemset((player, other_player),
                                 len(build.common_units(other_build)))

    close_builds = []
    for player_num, other_dist in enumerate(dist_matrix[0]):
        if other_dist > 20:
            player = player_map[player_num]
            close_builds.append(player_builds[player_id])
    
    import pdb;pdb.set_trace()

    pca = PCA()
    reduced = pca.fit_transform(scale(dist_matrix))
    cum_var = np.cumsum(np.round(pca.explained_variance_ratio_,
                                 decimals=4)*100)



if __name__ == '__main__':
    main()
