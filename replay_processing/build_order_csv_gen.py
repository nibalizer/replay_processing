import argparse
import csv
import glob
import hashlib
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
                        help="Path to directory to place csv files.",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    output_path = os.path.join(args.output_path, '%s.csv')
    replays = glob.glob('%s/**/*.SC2Replay' % args.replay_path,
                        recursive=True)
    for path in replays:
        path_hash = hashlib.sha256(path.encode('utf-8')).hexdigest()
        out_name = '%s-%s' % (path_hash, os.path.basename(path))
        try:
            gen_csv(path, output_path % out_name)
        except model.ReplayParseError as e:
            print('Replay parse error: %s' % e)
            continue


def gen_csv(replay_path, output_path):
    ignore_units = set([
        'AdeptPhaseShift',
        'BroodlingEscort',
        'CreepTumorQueen',
        'DisruptorPhased',
        'Egg',
        'ForceField',
        'InfestedTerransEgg',
        'KD8Charge',
        'Larva',
        'LiberatorAG',
        'LocustMPPrecursor',
        'LocustMPFlying',
        'LurkerBurrowed',
        'LurkerEgg',
        'OracleStasisTrap',
        'OverlordTransport',
        'ParasiticBombDummy',
        'PointDefenseDrone',
        'PylonOvercharged',
        'RavagerCocoon',
        'ThorAP',
        'TransportOverlordCocoon'
    ])

    with open(output_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=' ',
                               quotechar='|', quoting=csv.QUOTE_MINIMAL)

        replay = model.Replay(replay_path)

        if len(replay.players) != 2:
            print("Non 2 player game %s" % replay_path)
            return

        csvfile.write('# generated from replay file "%s"\n' % replay_path)
        csvwriter.writerow(('time', 'team', 'event_type', 'event_name'))
        events = list(replay.events)
        for unit_event in model.unit_events(events):
            time = unit_event.second
            team = unit_event.unit.owner.team_id
            try:
                ev_type = model.unit_to_type_string(unit_event.unit)
            except ValueError:
                try:
                    if (unit_event.unit.title in ignore_units or
                        unit_event.unit.title.startswith('Changeling') or
                        unit_event.unit.title.startswith('Shape')):
                        continue
                    else:
                        import pdb;pdb.set_trace()
                except AttributeError:
                    continue
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
