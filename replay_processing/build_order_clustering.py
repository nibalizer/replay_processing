import argparse
import collections
import csv
import glob
import heapq
import sys

import numpy as np
from sklearn.preprocessing import scale
from sklearn.decomposition import PCA

from sklearn.cluster import AffinityPropagation

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_dir",
                        help="Path to directory of build order csvs.",
                        type=str)
    parser.add_argument("--time-cutoff",
                        help="Seconds to stop considering data.",
                        type=int,
                        default=0)

    return parser.parse_args(args)


Unit = collections.namedtuple('Unit', ['type', 'name'])


BuildItem = collections.namedtuple('BuildItem', ['time', 'unit'])


class PlayerBuild(object):
    def __init__(self, player_id, map_id, map_player):
        self.player_id = player_id
        self.map_id = map_id
        self.map_player = map_player
        self._items = []
        self._unit_counts = None

    @property
    def items(self):
        return sorted(self._items)

    @property
    def unit_counts(self):
        if self._unit_counts is not None:
            return self._unit_counts
        unit_counts = collections.defaultdict(int)
        for ev in self._items:
            unit_counts[ev.unit] += 1
        self._unit_counts = unit_counts
        return unit_counts

    @property
    def units(self):
        return self.unit_counts.keys()

    def add_build_item(self, item):
        heapq.heappush(self._items, item)

    def common_units(self, other_build):
        return self.units & other_build.units

    def unit_count_distance(self, other_build):
        common_units = 0
        for unit, count in self.unit_counts.items():
            other_count = other_build.unit_counts.get(unit, 0)
            common_units += min(count, other_count)
        return common_units


class PlayerBuilds(object):
    def __init__(self):
        self._builds = {}

    def next_build(self, map_id, map_player):
        next_id = len(self._builds)
        next_build = PlayerBuild(next_id, map_id, map_player)
        self._builds[next_id] = next_build
        return next_build

    def get_by_player_id(self, player_id):
        return self._builds[player_id]

    def __len__(self):
        return len(self._builds)

    def items(self):
        return self._builds.items()


def main():
    args = parse_args(sys.argv[1:])

    builds = PlayerBuilds()

    for path in glob.glob('%s/**/*.csv' % args.csv_dir, recursive=True):
        with open(path, newline='') as infile:
            csvfile = csv.reader(infile, delimiter=' ', quotechar='|')
            try:
                next(csvfile)
                next(csvfile)
            except StopIteration:
                continue
            players = (builds.next_build(path, 0),
                       builds.next_build(path, 1))
            for row in csvfile:
                ev_time = int(row[0])
                if ev_time > 0 and (args.time_cutoff == 0 or ev_time <= int(args.time_cutoff)):
                    try:
                        player = players[int(row[1]) - 1]
                    except ValueError:
                        print('Invalid row in %s' % path)
                    unit = Unit(row[2], row[3])
                    build_item = BuildItem(row[0], unit)
                    player.add_build_item(build_item)

    dist_matrix = np.empty(shape=(len(builds), len(builds)))
    for player, build in builds.items():
        for other_player, other_build in builds.items():
            dist = build.unit_count_distance(other_build)
            dist_matrix.itemset((player, other_player), dist)

    scaled_dist = scale(dist_matrix)

    ap = AffinityPropagation(affinity='precomputed',
                             damping=.5)
    ap.fit(scaled_dist)

    builds_by_label = collections.defaultdict(list)
    for i, label in enumerate(ap.labels_):
        builds_by_label[label].append(builds.get_by_player_id(i))


    units_per_label = {}
    for label, label_builds in builds_by_label.items():
        unit_counts = collections.defaultdict(int)
        for build in label_builds:
            for unit in build.units:
                unit_counts[unit] += 1
        units_per_label[label] = sorted(unit_counts.items(),
                                        key=lambda x: x[1],
                                        reverse=True)

    brief_units_per_labels = {}
    for label, units_label in units_per_label.items():
        if len(units_label) > 0:
            max_units = units_label[0][1]
            brief_units_per_labels[label] = list(filter(
                lambda x: x[1] >= int(max_units * .6),
                units_label
            ))


    label_popularity = collections.defaultdict(int)
    for label in ap.labels_:
        label_popularity[label] += 1
    popular_labels = sorted(label_popularity.items(),
                            key=lambda x: x[1],
                            reverse=True)

    for label, popularity in popular_labels:
        center_build_id = ap.cluster_centers_indices_[label]
        center_build = builds.get_by_player_id(center_build_id)
        print("Label ID %d with popularity %d" % (label, popularity))
        print("\tCenter build:")
        print("\t\tMap: %s" % center_build.map_id)
        print("\t\tPlayer ID: %d" % (center_build.map_player + 1))
        print("\tPopular units:")
        try:
            for unit, popularity in brief_units_per_labels[label]:
                print("\t\t%s (%d)" % (unit, popularity))
        except KeyError:
            pass
        print("\tBuilds:")
        try:
            for build in builds_by_label[label]:
                print("\t\tMap: %s" % build.map_id)
                print("\t\tPlayer ID: %d" % (build.map_player + 1))
        except KeyError:
            pass
        print()


if __name__ == '__main__':
    main()
