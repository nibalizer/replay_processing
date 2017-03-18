import argparse
import collections
import itertools
import json
import msgpack
import os
import sys

from replay_processing import model

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("clustering_dir",
                        help="Path to directory of clustering data.",
                        type=str)
    parser.add_argument("replays_dir",
                        help="Path to directory of sha-named replays.",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    dest_dir = os.path.join(args.clustering_dir, 'replay_info')
    metadata_dir = os.path.join(dest_dir, 'metadata')
    events_dir = os.path.join(dest_dir, 'events')
    for _dir in (metadata_dir, events_dir):
        os.makedirs(_dir, exist_ok=True)

    for replay in model.replays_from_dir(args.replays_dir):
        try:
            replay_info = {
                'seconds': replay.seconds,
                'map_name': replay.map_name,
                'players': [str(x) for x in replay.players]
            }

        except Exception:
            print("Error processing replay %s" % replay.path)
        else:
            events = list(replay.events)
            unit_events = model.unit_events(events)
            upgrade_events = model.events_by_type(events,
                                                  ('UpgradeCompleteEvent', ))

            met_dest_dir = os.path.join(metadata_dir, replay.id[0])
            os.makedirs(met_dest_dir, exist_ok=True)

            ev_dest_dir = os.path.join(events_dir, replay.id[0])
            os.makedirs(ev_dest_dir, exist_ok=True)

            metadata_dest = os.path.join(met_dest_dir,
                                         '.'.join((replay.id, 'json')))
            ev_dest = os.path.join(ev_dest_dir, '.'.join((replay.id, 'json')))
            with open(metadata_dest, 'wb') as fh:
                msgpack.pack(replay_info, fh)
            with open(ev_dest, 'wb') as fh:
                events = collections.deque()
                for event in unit_events:
                    try:
                        unit_type = model.unit_to_type_string(event.unit)
                    except ValueError:
                        continue
                    events.append(('unit',
                                   event.second,
                                   event.unit.owner.team_id,
                                   event.unit.title,
                                   unit_type))
                for event in upgrade_events:
                    events.append(('upgrade',
                                   event.second,
                                   event.player.team_id,
                                   event.upgrade_type_name))
                msgpack.pack(list(events), fh)
