import collections
import glob
import itertools
import os

import sc2reader

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


class Replay(object):
    def __init__(self, path):
        self.path = path
        self._parsed_replay_obj = None

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def _parsed_replay(self):
        if self._parsed_replay_obj is None:
            replay = sc2reader.load_replay(self.path)
            self._parsed_replay_obj = replay
        return self._parsed_replay_obj

    @property
    def events(self):
        return self._parsed_replay.events


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
    'BarracksReactor': 'building',
    'BarracksTechLab': 'building',
    'RoboticsFacility': 'building',
    'FactoryReactor': 'building',
    'FactoryTechLab': 'building',
    'StarportReactor': 'building'
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
