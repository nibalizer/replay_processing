#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import spawningtool.parser
from sc2scan import populate_build_data, map_process, is_korean_map


def classify_matchup(result):
    races = []
    for player in result['players'].values():
        if debug:
            print "debug:", player['name'], '(', player["race"], ')'
        races.append(player['race'])

    matchup = sorted(races)[0][0]
    matchup += "v"
    matchup += sorted(races)[1][0]
    if debug:
        print "debug: matchup is:", matchup
    return matchup


def print_results(result):
    "print out a column of data"
    both_data = []
    for player in [1, 2]:
        opponent = 2 if player == 1 else 1
        if debug:
            print "debug: Player is ", player
            print "debug: Opponent is ", opponent

        # Our main data hash
        data = {}

        # Map
        data['map'] = map_process(unicode(result['map']), debug)

        # Matchup
        data['matchup'] = classify_matchup(result)

        # Player, opponent, and race
        data['player'] = result['players'][player]['name']
        data['opponent'] = result['players'][opponent]['name']
        data['player_race'] = result['players'][player]['race']
        data['opponent_race'] = result['players'][opponent]['race']

        # Winner
        if result['players'][player]['is_winner']:
            data['Winner'] = "True"
        elif result['players'][opponent]['is_winner']:
            data['Winner'] = "False"
        else:
            data['Winner'] = 'unknown'

        # Game Length(seconds)
        data['Game Length(seconds)'] = str(result['frames'] / 16.)

        # Region(eu, kr, na)
        data['region'] = result['region']

        # Category (ladder, custom, etc)
        data['game_category'] = result['category']

        # StarCraft version information
        data['build'] = str(result['build'])
        data['baseBuild'] = str(result['baseBuild'])

        # The UTC time (according to the client NOT the server) thaat the game
        # was ended as represented by the Unix OS
        data['unix_timestamp'] = str(result['unix_timestamp'])

        data.update(populate_build_data(result['players'][player], debug))
        both_data.append(data)

    return both_data


def dump(fieldnames, data):
    orderd_data = []
    try:
        for i in fieldnames:
            orderd_data.append(unicode(data[i]))
        print ",".join(orderd_data)
    except KeyError:
        from pdb import set_trace; set_trace()


def main():
    # Turn on debug from environment variable
    debug = False
    sc2debug = os.environ.get("SC2DEBUG")
    if sc2debug is not None:
        debug = True

    # Limit to a small set of replays from environment variable
    small_set = os.environ.get("SC2SMALL")
    if small_set is not None:
        small_set = int(small_set)

    # If SC2REPLAYS is set, search that dir instead
    sc2replays = os.environ.get("SC2REPLAYS")
    if sc2replays is not None:
        replay_dir = sc2replays
    else:
        replay_dir = 'replays'

    match_stats = {
        "TvT": 0,
        "ZvZ": 0,
        "PvP": 0,
        "PvT": 0,
        "TvZ": 0,
        "PvZ": 0,
    }

    count = 0
    replay_files = []
    error_replays = []
    korean_maps = []
    results = []

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(replay_dir):
        path = root.split('/')
        for file in files:
            if file.endswith(".SC2Replay"):
                replay_files.append(root + "/" + file)

    # Shuffle the replay files. This helps with local testing since we'll see
    # more variation in the first few seconds of running the program
    random.shuffle(replay_files)

    fieldnames = ['map',
                  'first_army_unit_supply',
                  'Game Length(seconds)',
                  'baseBuild',
                  'region',
                  'Winner',
                  'first_army_unit',
                  'first_army_unit_time',
                  'player',
                  'game_category',
                  'build',
                  'unix_timestamp',
                  'player_race',
                  'matchup',
                  'opponent_race',
                  'opponent',
                  'first_tech_path',
                  'Carriers count',
                  'Carrier timing',
                  'Carriers',
                  'replay_file']

    print ",".join(fieldnames)

    for replay in replay_files[:small_set:]:
        count += 1
        try:
            f = spawningtool.parser.parse_replay(replay)
            if debug:
                print "debug:", replay
                print "debug: number of players detected: ", len(f['players'])

            # We don't want any not 1v1 matches
            if f['game_type'] != '1v1':
                error_replays.append(replay)
                continue

            # We don't want any not 1v1 matches
            if len(f['players']) != 2:
                error_replays.append(replay)
                continue

            # Keep track of all the map names not translated to english
            if is_korean_map(f['map']):
                korean_maps.append(unicode(f['map']))

            # Keep track of matchup stats(really don't need this anymore)
            match_stats[classify_matchup(f)] += 1

            for player_side in print_results(f):
                data = {}
                data['replay_file'] = replay
                data.update(player_side)
                #results.append(data)
                dump(fieldnames, data)
        except (spawningtool.exception.ReadError,
                UnicodeEncodeError,
                IndexError,
                KeyError,
                AttributeError):
            error_replays.append(replay)
            continue
    print "match stats:", match_stats
    print "total replays:", count, "error replays:", len(error_replays), "error percent:" , len(error_replays)/float(count)
    print "Error replays:", error_replays
    print "Korean replays", 
    for map in korean_maps:
        print unicode(map),
    print


if __name__ == "__main__":
    main()
