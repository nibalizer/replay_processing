import itertools

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

class Replay(object):
    def __init__(self, path):
        self._path = path
        self._parsed_replay_obj = None

    @property
    def _parsed_replay(self):
        if self._parsed_replay_obj is None:
            replay = sc2reader.load_replay(self._path)
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
    events = events_by_type(events, ('UnitBornEvent', 'UnitDoneEvent'))
    events = filter(lambda x: x.unit.name not in BEACON_UNITS, events)
    if not include_npc:
        return filter(lambda x: x.unit.owner is not None, events)
    return events
