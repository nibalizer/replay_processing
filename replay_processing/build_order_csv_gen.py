import argparse
import csv
import logging
import os
import sys

from replay_processing import model

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("replay_path",
                        help="Path to replay directory.",
                        type=str)
    parser.add_argument("output_path",
                        help="Path to write out CSV to.",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    ignore_units = set([
        'AdeptPhaseShift',
        'DisruptorPhased',
        'KD8Charge',
        'LiberatorAG',
        'PylonOvercharged'
    ])

    with open(args.output_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=' ',
                               quotechar='|', quoting=csv.QUOTE_MINIMAL)

        replay = model.Replay(args.replay_path)
        csvwriter.writerow(('time', 'team', 'event_type', 'event_name'))
        events = list(replay.events)
        for unit_event in model.unit_events(events):
            time = unit_event.second
            team = unit_event.unit.owner.team_id
            try:
                ev_type = model.unit_to_type_string(unit_event.unit)
            except ValueError:
                if unit_event.unit.title in ignore_units:
                    pass
                else:
                    import pdb;pdb.set_trace()
            ev_name = unit_event.unit.title

            csvwriter.writerow((time, team, ev_type, ev_name))

        upgrade_events = model.events_by_type(events,
                                              ('UpgradeCompleteEvent', ))
        for upgrade_event in upgrade_events:
            time = upgrade_event.second
            team = upgrade_event.player.team_id
            ev_type = 'upgrade'
            ev_name = upgrade_event.upgrade_type_name

            csvwriter.writerow((time, team, ev_type, ev_name))


if __name__ == '__main__':
    main()
