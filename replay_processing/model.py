import collections
import glob
import itertools
import json
import os

import sc2reader


class ReplayParseError(Exception):
    def __init__(self, replay_path, exc):
        super(ReplayParseError, self).__init__(
            'Failed to parse replay file %s' % replay_path
        )
        self.replay_path = replay_path
        self.exc = exc


# I have no idea what these are, but they always exist as unit events
# before the game begins
BEACON_UNITS = set([
    'BeaconArmy',
    'BeaconDefend',
    'BeaconAttack',
    'BeaconHarass',
    'BeaconIdle',
    'BeaconAuto',
    'BeaconDetect',
    'BeaconScout',
    'BeaconClaim',
    'BeaconExpand',
    'BeaconRally',
    'BeaconCustom1',
    'BeaconCustom2',
    'BeaconCustom3',
    'BeaconCustom4'
])


UNIT_CREATED_EVENT_TYPES = [
    'UnitBornEvent',
    'UnitDoneEvent'
]


def replays_from_dir(root_dir):
    return map(Replay,
               glob.glob("%s/**/*.SC2Replay" % root_dir), recursive=True)


def _replay_parse_guard(fn):
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except (IndexError, AttributeError) as e:
            raise ReplayParseError(self.path, e)
    return wrapper


class Replay(object):
    def __init__(self, path):
        self.path = path
        self._parsed_replay_obj = None

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    @_replay_parse_guard
    def seconds(self):
        return self._parsed_replay.real_length.seconds

    @property
    def _parsed_replay(self):
        if self._parsed_replay_obj is None:
            replay = sc2reader.load_replay(self.path)
            self._parsed_replay_obj = replay
        return self._parsed_replay_obj

    @property
    @_replay_parse_guard
    def events(self):
        return self._parsed_replay.events

    @property
    @_replay_parse_guard
    def players(self):
        return self._parsed_replay.players


def event_type_names(events):
    type_names = set()
    for ev in events:
        if ev.name not in type_names:
            type_names.add(ev.name)
            yield ev.name


def events_by_type(events, include_types=None, exclude_types=None):
    incl = set(include_types or [])
    excl = set(exclude_types or [])
    return filter(lambda x: x.name in incl and x.name not in excl, events)


def unit_events(events, include_npc=False):
    events = events_by_type(events, UNIT_CREATED_EVENT_TYPES)
    events = filter(lambda x: x.unit.name not in BEACON_UNITS, events)
    if not include_npc:
        return filter(lambda x: x.unit.owner is not None, events)
    return events


def all_unit_created_events_by_type(events):
    army_evs = collections.deque()
    building_evs = collections.deque()
    worker_evs = collections.deque()

    for event in unit_events(events):
        if event.is_army:
            army_evs.append(event)
        elif event.is_building:
            building_evs.append(event)
        elif event.is_worker:
            worker_evs.append(event)

    return army_evs, building_evs, worker_evs


_force_unit_types = {
    'MULE': 'worker',
    'Adept': 'army',
    'AutoTurret': 'army',
    'Cyclone': 'army',
    'BarracksReactor': 'building',
    'BarracksTechLab': 'building',
    'Disruptor': 'army',
    'FactoryReactor': 'building',
    'FactoryTechLab': 'building',
    'Interceptor': 'army',
    'Liberator': 'army',
    'Lurker': 'army',
    'LurkerDen': 'building',
    'Nuke': 'army',
    'Ravager': 'army',
    'RoboticsFacility': 'building',
    'StarportReactor': 'building',
    'StarportTechLab': 'building',
    'Reactor': 'building',
    'TechLab': 'building',
    'TemplarArchive': 'building'
}


def unit_to_type_string(unit):
    if unit.is_army:
        return 'army'
    if unit.is_building:
        return 'building'
    if unit.is_worker:
        return 'worker'

    try:
        return _force_unit_types[unit.title]
    except KeyError:
        raise ValueError('Not a unit!')


class ClusteringBuild(object):
    @staticmethod
    def from_map_player_key(key, clustering_data):
        map_player, map_id = key.split('@')
        return ClusteringBuild(map_player, map_id, clustering_data)

    def __init__(self, map_player, map_id, clustering_data):
        self.map_player = map_player
        self.map_id = map_id
        self.clustering_data = clustering_data

    @property
    def affinity(self):
        return self.clustering_data['affinity']

    @property
    def replay_path(self):
        return os.path.join(replays_dir,
                            self.map_id[0],
                            '.'.join(self.map_id, 'SC2Replay'))

    @property
    def csv_path(self):
        return os.path.join(csv_dir,
                            self.map_id[0],
                            '.'.join(self.map_id, 'csv'))


class ClusteringLabel(object):
    def __init__(self, label, data):
        self.label = label
        self.data = data

    @property
    def center(self):
        center_key = self.data['center']
        center_data = self.data['builds'][center_key]
        return ClusteringBuild.from_map_player_key(center_key,
                                                   center_data)

    @property
    def builds(self):
        return [ClusteringBuild.from_map_player_key(key, val) for key, val in
                self.data['builds'].items()]

    def __len__(self):
        return len(self.data['builds'])


class ClusteringData(object):
    def __init__(self, path):
        self.path = path
        self._raw_data = None

    @property
    def raw_data(self):
        if self._raw_data is None:
            with open(self.path) as fh:
                self._raw_data = json.load(fh)
        return self._raw_data

    @property
    def labels(self):
        return {label: ClusteringLabel(label, label_data) for label, label_data
                in self.raw_data['labels'].items()}


class ClusteringDataDir(object):
    def __init__(self, path):
        self.path = path

    def clustering_data(self, name):
        return ClusteringData(os.path.join(self.path,
                                           'clusterings',
                                           '.'.join((name, 'json'))))
