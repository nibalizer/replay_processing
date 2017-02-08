from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
import logging
import sys
import threading
import traceback

import spawningtool.parser
import spawningtool.exception
from replay_processing.sc2scan import is_korean_map, map_process, populate_build_data
from collections import Counter

FIELD_NAMES = ['map',
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


def classify_matchup(parsed):
    races = [data["race"] for data in parsed["players"].values()]
    return "v".join(race[0] for race in sorted(races))


def not_one_on_one(parsed_data):
    return parsed_data["game_type"] != "1v1" or len(parsed_data["players"]) != 2


def extract_player_data(result, player, logger, debug=False):
    # TODO: what about other types of games?
    opponent = 2 if player == 1 else 1

    # Our main hash
    data = {}
    # Map
    # fix map_process debug handling
    data["map"] = map_process(result["map"], logger)

    # Matchup
    data["matchup"] = classify_matchup(result)

    # Player, opponent, and race
    data['player'] = result['players'][player]['name']
    data['opponent'] = result['players'][opponent]['name']
    data['player_race'] = result['players'][player]['race']
    data['opponent_race'] = result['players'][opponent]['race']

    # Winner
    # TODO: Why does this have to be string? Can we refactor this?
    # Winner
    if result['players'][player]['is_winner']:
        data['Winner'] = "True"
    elif result['players'][opponent]['is_winner']:
        data['Winner'] = "False"
    else:
        data['Winner'] = 'unknown'

    # Game Length(seconds)
    data["Game Length(seconds)"] = str(result["frames"] / 16.)

    # Region (eu, kr, na)
    data["region"] = result["region"]

    # Category (ladder, custom, etc)
    data['game_category'] = result['category']

    # StarCraft version information
    data['build'] = str(result['build'])
    data['baseBuild'] = str(result['baseBuild'])

    # The UTC time (according to the client NOT the server) thaat the game
    # was ended as represented by the Unix OS
    data['unix_timestamp'] = str(result['unix_timestamp'])

    # Fix populate_build_data debug handling
    data.update(populate_build_data(result['players'][player], logger))

    return data


def dump(data, outfile):
    # TODO: Fix this up
    outfile.write(",".join([str(data[field]) for field in FIELD_NAMES]))
    outfile.write("\n")


def print_results(result, logger):
    # print out a column of data
    both_data = [extract_player_data(result, k, logger) for k in [1, 2]]
    return both_data


def worker(filename, all_replays, logger):
    # TODO: This can be set up better
    data = {
        "sides": []
    }
    num_players = 0
    error_replay = False
    korean = False
    map_name = None
    matchup = None
    try:
        # Run the spawning tool to parse our replay files
        parsed = spawningtool.parser.parse_replay(filename)
        num_players = len(parsed["players"])
        logger.debug(filename)
        logger.debug("Number of players in match: {0}".format(num_players))

        # We don't want any not 1v1 matches if all_replays flag is false
        if not_one_on_one(parsed) and not all_replays:
            error_replay = True
            return data, num_players, error_replay, is_korean_map, map_name, matchup

        # Keep track of all the Korean maps (??)
        korean = is_korean_map(parsed["map"])
        map_name = parsed['map']

        # Keep track of matchup stats(really don't need this anymore)
        matchup = classify_matchup(parsed)
        logger.debug("Matchup: {0}".format(matchup))

        for player_side in print_results(parsed, logger):
            player_data = {}
            player_data['replay_file'] = filename
            player_data.update(player_side)
            data["sides"].append(player_data)
            # results.append(data)

        return data, num_players, error_replay, korean, map_name, matchup
    except (spawningtool.exception.ReadError, IndexError, KeyError, AttributeError) as e:
        traceback.print_exc()
        error_replay = True
        return data, num_players, error_replay, korean, map_name, matchup


def parse_replays(root_dir, num_threads,
                  logger=logging.getLogger("replayParser"),
                  max_replays=None, all_replays=False,
                  outfile=None):

    outfile = outfile or sys.stdout
    dump_lock = threading.Lock()
    # Run our replay parsing in a thread pool executor with 5 workers.
    match_data = []
    count = 0
    errors = 0
    error_replays = []
    match_stats = Counter()
    korean_replays = []

    outfile.write(','.join(FIELD_NAMES))
    outfile.write('\n')

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_replay = {}
        replay_files = glob.glob("{root_dir}/**/*.SC2Replay".format(root_dir=root_dir), recursive=True)
        replay_files = replay_files[:max_replays] if max_replays is not None else replay_files
        for filename in replay_files:
            # mark each future with the replay filename
            future_to_replay[executor.submit(worker, filename, all_replays, logger)] = filename

        for future in as_completed(future_to_replay):
            r_file = future_to_replay[future]
            data, num_players, error, in_korean, map_name, matchup = future.result()
            if error:
                count += 1
                errors = errors + 1
                error_replays.append(r_file)
                continue
            else:
                match_stats[matchup] += 1
                count += 1
                for item in data["sides"]:
                    # TODO: Instead of this, should just do a full dump at the end and write a proper CSV file
                    with dump_lock:
                        dump(item, outfile)
                # Take data from futures and add to proper
                match_data.append(data)
                if in_korean:
                    korean_replays.append(map_name)

        return match_data, count, errors, error_replays, match_stats, korean_replays
