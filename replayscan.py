import os
import spawningtool.parser
from sc2scan import populate_build_data


def classify_matchup(result):
    races = []
    for player in result['players'].values():
        if debug:
            print('debug:{} ({})'.format(player['name'], player['race']))
        races.append(player['race'])

    matchup = sorted(races)[0][0]
    matchup += "v"
    matchup += sorted(races)[1][0]
    if debug:
        print "debug: matchup is:", matchup
    return matchup


def print_results(result, header_printed):
    "print out a column of data"
    for player in [1, 2]:
        opponent = 2 if player == 1 else 1
        if debug:
            print "debug: Player is ", player
            print "debug: Opponent is ", opponent

        # Our main data hash
        data = {}

        # Map
        data['map'] = result['map']

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

        if not header_printed:
            print ",".join(data.keys())
            header_printed = True
        print ",".join(data.values())

    return header_printed


if __name__ == "__main__":
    debug = False
    sc2debug = os.environ.get("SC2DEBUG")
    if sc2debug is not None:
        debug = True

    header_printed = False

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

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk("replays"):
        path = root.split('/')
        for file in files:
            if file.endswith(".SC2Replay"):
                replay_files.append(root + "/" + file)

    for replay in replay_files:
        count += 1
        try:
            f = spawningtool.parser.parse_replay(replay)
            if debug:
                print "debug: number of players detected: ", len(f['players'])

            # We don't want any not 1v1 matches
            if f['game_type'] != '1v1':
                error_replays.append(replay)
                continue

            # We don't want any not 1v1 matches
            if len(f['players']) != 2:
                error_replays.append(replay)
                continue

            match_stats[classify_matchup(f)] += 1
            header_printed = print_results(f, header_printed)
        except (spawningtool.exception.ReadError,
                AttributeError,
                UnicodeEncodeError,
                KeyError,
                IndexError):
            error_replays.append(replay)
            continue
    print error_replays
    print match_stats
    print count
