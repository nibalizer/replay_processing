import argparse
import collections
import csv
import glob
import heapq
import json
from math import log
import msgpack
import os
import sys

import numpy as np
from sklearn.preprocessing import scale
from sklearn.cluster import AffinityPropagation

from replay_processing import model
from replay_processing.model import Unit, BuildItem

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("clustering_dir",
                        help="Path to clustering data directory",
                        type=str)
    parser.add_argument("output_path",
                        help="Path to json clustering output destination.",
                        type=str)
    parser.add_argument("--time-cutoff",
                        help="Seconds to stop considering data.",
                        type=int,
                        default=0)
    parser.add_argument("--affinity-between",
                         help="Two player@map_ids separated by comma to "
                              "compute affinity between",
                         type=str)

    return parser.parse_args(args)


class PlayerBuild(object):

    def __init__(self, player_id, map_id, map_player):
        self.player_id = player_id
        self.map_id = map_id
        self.map_player = map_player
        self._items = []
        self._unit_counts = None
        self._events_by_unit = None

    @property
    def map_player_key(self):
        return '@'.join((str(self.map_player + 1), self.map_sha))

    @property
    def map_sha(self):
        return os.path.basename(self.map_id).split('.', 1)[0]

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

    def load_events_file(self, events_path, ev_time_cutoff):
        with open(events_path, 'rb') as events_file:
            events = msgpack.unpack(events_file)

            for ev_ndx, event in enumerate(events):
                try:
                    ev_time = event[1]
                    unit_name = event[3].decode('utf-8')
                    ev_player_id = event[2] - 1
                    unit_type = event[0].decode('utf-8')
                except (ValueError, TypeError, IndexError):
                    print('Invalid row in %s' % events_path)
                    continue
                else:
                    if (ev_player_id == self.map_player and
                        unit_name not in model.IGNORE_UNITS and
                        ev_time > 0 and
                        (ev_time_cutoff == 0 or ev_time <= ev_time_cutoff)):
                        if unit_type != 'upgrade':
                             unit_type = event[4].decode('utf-8')
                        unit = Unit(unit_type, unit_name)
                        if (unit.type == 'worker' or
                            unit.name.startswith('Changeling') or
                            unit.name.startswith('Shape') or
                            unit.name.startswith('Reward')):
                            continue
                        build_item = BuildItem(ev_ndx, ev_time, unit)
                        self.add_build_item(build_item)

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

    def unit_events_affinity(self, my_events, other_events, pdb=False):
        score = 0
        max_score = max(len(my_events), len(other_events))
        used_events = set()
        for my_event in my_events:
            closest = None
            closest_dist = 0
            for other_event in other_events:
                if other_event in used_events:
                    continue
                if (closest is None or
                    abs(closest.time - my_event.time) < closest_dist):
                    closest = other_event
                    closest_dist = abs(closest.time - my_event.time)
                
            if closest != None:
                used_events.add(closest)
                ev_score = 1 / max(1, closest_dist / 420)
                if pdb and ev_score != 1:
                    import pdb;pdb.set_trace()
                score += ev_score

        if max_score is 0:
            return 0

        if pdb and score / max_score != 1:
            import pdb;pdb.set_trace()
        return score / max_score

    def unit_type_ratios(self, other_build, unit_popularity):
        my_unit_events = self.events_by_unit
        other_unit_events = other_build.events_by_unit

        all_units = set(my_unit_events.keys())
        all_units.union(set(other_unit_events.keys()))

        max_score = 0
        score = 0

        for unit in all_units:
            cur_events = my_unit_events.get(unit, [])
            other_cur_events = other_unit_events.get(unit, [])

            weight = unit_popularity.get(unit, 1)
            if unit.type == 'building' or unit.type =='upgrade':
                weight /= 10
            weight = log(weight)
            unit_score = self.unit_events_affinity(cur_events,
                                                   other_cur_events)

            if other_build.map_id == self.map_id and self.map_player == other_build.map_player and unit_score != 0:
                unit_score = self.unit_events_affinity(cur_events,
                                                       other_cur_events,
                                                       pdb=True)

            score += unit_score / weight
            max_score += 1 / weight

        if max_score == 0:
            return 0

        score = score / max_score
        if score == 1 and self.map_id != other_build.map_id:
            import pdb;pdb.set_trace
        return score


class PlayerBuilds(object):
    def __init__(self):
        self._builds = {}

    def build_from_events_file(self, map_player, events_path, ev_time_cutoff):
        map_id = os.path.basename(events_path).split('.')[0]
        build = self.next_build(map_id, map_player)
        build.load_events_file(events_path, ev_time_cutoff)
        return build

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
            for unit, count in build.unit_counts.items():
                counts[unit] = counts.get(unit, 0) + count
        return counts


def main():
    args = parse_args(sys.argv[1:])

    builds = PlayerBuilds()

    events_dir = os.path.join(args.clustering_dir, 'replay_info', 'events')
    clustering_dir = model.ClusteringDataDir(args.clustering_dir)
    replays_info = clustering_dir.replays_info
    ev_cutoff = int(args.time_cutoff)
    unit_popularity = clustering_dir.unit_popularity

    if args.affinity_between:
        map1, map2 = args.affinity_between.split(',')
        player_1, map_1 = map1.split('@')
        player_2, map_2 = map2.split('@')
        player_1 = int(player_1) - 1
        player_2 = int(player_2) - 1
        events_1 = os.path.join(events_dir, map_1[0], '.'.join((map_1, 'json')))
        events_2 = os.path.join(events_dir, map_2[0], '.'.join((map_2, 'json')))
        build_1 = builds.build_from_events_file(player_1, events_1, ev_cutoff)
        build_2 = builds.build_from_events_file(player_2, events_2, ev_cutoff)
        affinity = build_1.unit_type_ratios(build_2, unit_popularity)
        print("Affinity: %f" % affinity)
        return

    print("Loading builds...",)
    for path in glob.glob('%s/**/*.json' % events_dir, recursive=True):
        with open(path, 'rb') as events_file:
            map_path = os.path.basename(path).split('.')[0]
            replay_info = replays_info.replay(map_path)
            if args.time_cutoff != 0 and replay_info.seconds < args.time_cutoff:
                print("Replay %s too short %d seconds" % (map_path,
                                                          replay_info.seconds))
                continue
            players = (builds.build_from_events_file(0, path,
                                                     ev_cutoff),
                       builds.build_from_events_file(1, path,
                                                     ev_cutoff))
    print("done")

    dist_matrix = np.empty(shape=(len(builds), len(builds)))

    # Distance from a->b == distance from b->a
    distance_cache = {}

    print("Building affinity matrix...")
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
    print("done")

    scaled_dist = dist_matrix

    ap = AffinityPropagation(affinity='precomputed',
                             damping=.5)
    print("Running clustering...")
    ap.fit(scaled_dist)
    print("done")

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

    label_unit_avgs = {}
    for label, units in units_per_label.items():
        labl_unit_avgs[label] = units / len(builds_by_label[label])

    with open(args.output_path, 'w') as fh:
        labels_output = {}
        for label, _builds in builds_by_label.items():
            _builds_out = {}
            for _build in _builds:
                center_build_id = ap.cluster_centers_indices_[label]
                center_build = builds.get_by_player_id(center_build_id)
                try:
                    dist = distance_cache[(_build.player_id,
                                           center_build.player_id)]
                except KeyError:
                    dist = distance_cache[(center_build.player_id,
                                           _build.player_id)]
                _builds_out[_build.map_player_key] = { 'affinity': dist }
            labels_output[str(label)] = {
                'builds': _builds_out,
                'center': center_build.map_player_key
            }
        output = {
            'labels': labels_output,
            'confidence': 1,
            'labl_unit_avgs': label_unit_avgs
        }
        json.dump(output, fh, indent=4, separators=(',', ': '))



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
