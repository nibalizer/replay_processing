import argparse
import collections
import csv
import glob
import heapq
from math import log
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
        self._events_by_unit = None

    @property
    def items(self):
        return sorted(self._items)

    @property
    def unit_counts(self):
        if self._unit_counts is not None:
            return self._unit_counts
        unit_counts = {}
        for ev in self._items:
            unit_counts[ev.unit] = unit_counts.get(ev.unit, 0) + 1
        self._unit_counts = unit_counts
        return unit_counts

    @property
    def events_by_unit(self):
        if self._events_by_unit is not None:
            return self._events_by_unit

        self._events_by_unit = {}
        for item in iter(self.items):
            unit_events = self._events_by_unit.get(item.unit)
            if unit_events is None:
                unit_events = collections.deque()
            unit_events.append(item)
            self._events_by_unit[item.unit] = unit_events

        return self._events_by_unit

    @property
    def units(self):
        return self.unit_counts.keys()

    def add_build_item(self, item):
        heapq.heappush(self._items, item)

    def common_units(self, other_build):
        return self.units & other_build.units

    def items_before(self, time):
        for item in self.items:
            if item.time > time:
                return
            yield item

    def unit_count_similarity(self, other_build):
        common_units = 0
        for unit, count in self.unit_counts.items():
            other_count = other_build.unit_counts.get(unit, 0)
            comm_cnt = min(count, other_count)
            comm_cnt = min(comm_cnt, 5)
            common_units += .5 * self.harmonic_sum(comm_cnt)
        return common_units

    def harmonic_sum(self, n):
        "Taken from https://en.wikipedia.org/wiki/Harmonic_number"
        if n == 0:
            return 0
        gamma = 0.5772156649
        return gamma + log(n) + 0.5 / n - 1. / (12 * n**2) + 1. / (120 * n**4)

    def unit_type_ratios(self, other_build, unit_popularity):
        my_unit_events = self.events_by_unit
        other_unit_events = other_build.events_by_unit

        all_units = set(my_unit_events.keys())
        all_units.union(set(other_unit_events.keys()))

        max_score = 0
        score = 0

        for unit in all_units:
            unit_count = len(my_unit_events.get(unit, []))
            other_unit_count = len(other_unit_events.get(unit, []))

            weight = unit_popularity.get(unit, 1)
            unit_score = min(unit_count, other_unit_count) / weight
            score += unit_score
            max_score += max(unit_count, other_unit_count) / weight

        if max_score == 0:
            return 0

        score = score / max_score
        if score == 1 and self.map_id != other_build.map_id:
            import pdb;pdb.set_trace
        return score


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

    def unit_build_popularity_counts(self):
        counts = {}
        for build_id, build in self._builds.items():
            for unit in build.units:
                counts[unit] = counts.get(unit, 0) + 1
        return counts


def main():
    args = parse_args(sys.argv[1:])

    builds = PlayerBuilds()

    for path in glob.glob('%s/**/*.csv' % args.csv_dir, recursive=True):
        with open(path, newline='') as infile:
            csvfile = csv.reader(infile, delimiter=' ', quotechar='|')
            try:
                firstline = infile.readline()[:-1]
                next(csvfile)
            except StopIteration:
                continue
            map_path = firstline.split('"', 1)[1][:-1]
            players = (builds.next_build(map_path, 0),
                       builds.next_build(map_path, 1))
            for row in csvfile:
                ev_time = int(row[0])
                if ev_time > 0 and (args.time_cutoff == 0 or ev_time <= int(args.time_cutoff)):
                    try:
                        player = players[int(row[1]) - 1]
                    except (ValueError, IndexError):
                        print('Invalid row in %s' % path)
                    unit = Unit(row[2], row[3])
                    build_item = BuildItem(ev_time, unit)
                    player.add_build_item(build_item)

    unit_popularity = builds.unit_build_popularity_counts()

    dist_matrix = np.empty(shape=(len(builds), len(builds)))

    # Distance from a->b == distance from b->a
    distance_cache = {}

    for player, build in builds.items():
        for other_player, other_build in builds.items():
            try:
                dist = distance_cache[(build.player_id, other_build.player_id)]
            except KeyError:
                try:
                    dist = distance_cache[(other_build.player_id,
                                           build.player_id)]
                except KeyError:
                    dist = build.unit_type_ratios(other_build, unit_popularity)
                    distance_cache[(build.player_id,
                                    other_build.player_id)] = dist
            dist_matrix.itemset((player, other_player), dist)

    scaled_dist = dist_matrix

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
        print("\t\tPlayer ID: %d, Map %s" % ((center_build.map_player + 1),
                                             center_build.map_id))
        print("\tPopular units:")
        try:
            for unit, popularity in brief_units_per_labels[label]:
                print("\t\t%s (%d)" % (unit, popularity))
        except KeyError:
            pass
        print("\tBuilds:")
        try:
            label_builds = builds_by_label[label]
        except KeyError:
            pass
        for build in label_builds:
            try:
                dist = distance_cache[(build.player_id,
                                       center_build.player_id)]
            except KeyError:
                dist = distance_cache[(center_build.player_id,
                                       build.player_id)]
            print("\t\tAffinity: %f Player ID: %d, Map %s" % (
                dist, (build.map_player + 1), build.map_id)
            )
        print()


if __name__ == '__main__':
    main()
