import os
import spawningtool.parser


def classify_matchup(result):
    #print result['players']
    races = []
    for player in result['players'].values():
        if debug:
            print('debug:{} ({})'.format(player['name'], player['race']))
        races.append(player['race'])

    #from pdb import set_trace; set_trace()
    matchup = sorted(races)[0][0]
    matchup += "v"
    matchup += sorted(races)[1][0]
    #print matchup
    return matchup


def write_builds(result):
    matchup = classify_matchup(result)
    races = []
    for player in result['players'].values():
        races.append(player['race'])

    #print "races:",races
    for player in result['players'].values():
        local_races = []
        for race in races:
            local_races.append(race)
        local_races.remove(player['race'])
        # print "matchup is", player['race'], 'vs', local_races[0]
        short_matchup =  player['race'][0] + "v" + local_races[0][0]
        print "short matchup is", short_matchup
        print "Play result: ", player['is_winner']
        print('{} ({})'.format(player['name'], player['race']))
        filename = "out/" + short_matchup + "/" + str(count)
        f = open(filename, 'w')
        f.write('{} ({})\n'.format(player['name'], player['race']))
        f.write( "Short matchup: {0}\n".format(short_matchup))
        f.write( "Game id: {0}\n".format(count))
        f.write("Player won: {0}\n".format(player['is_winner']))
        if player['clock_position'] is not None:
            print('Start Position: {}:00'.format(player['clock_position']))
            f.write("Start Position: {}:00\n".format(player['clock_position']))
        for event in player['buildOrder']:
            if not event['is_worker']:
                print('{} {} {}{}'.format(
                    event['supply'],
                    event['time'],
                    event['name'],
                    ' (Chronoboosted)' if event['is_chronoboosted'] else ''
                ))
                f.write('{} {} {}{}\n'.format(
                    event['supply'],
                    event['time'],
                    event['name'],
                    ' (Chronoboosted)' if event['is_chronoboosted'] else ''
                ))
        f.close()

        print('')

def print_builds(result):
    for player in result['players'].values():
        print('{} ({})'.format(player['name'], player['race']))
        if player['clock_position'] is not None:
            print('Start Position: {}:00'.format(player['clock_position']))
        print('')


def print_units_lost(result):
    for player in result['players'].values():
        print('{} ({})'.format(player['name'], player['race']))
        for event in player['unitsLost']:
                print('{} {} killed by {}'.format(
                    event['time'],
                    event['name'],
                    event['killer']
                ))
        print('')

def populate_build_data(result):
    pass


def print_results(result, header_printed):
    "print out a column of data"
    for player in [1, 2]:
        opponent = 2 if player == 1 else 1
        # from pdb import set_trace; set_trace()
        if debug:
            print "debug: Player is ", player
            print "debug: Opponent is ", opponent
        data = {}
        data['map'] = result['map']
        data['matchup'] = classify_matchup(result)
        # player_1, player_2 = result['players'][1]['name'], result['players'][2]['name']
        # player_1_race, player_2_race = 
        data['player'] = result['players'][player]['name']
        data['opponent'] = result['players'][opponent]['name']
        data['player_race'] = result['players'][player]['race']
        data['opponent_race'] = result['players'][opponent]['race']

        if result['players'][player]['is_winner']:
            data['Winner'] = "True"
        elif result['players'][opponent]['is_winner']:
            data['Winner'] = "False"
        else:
            data['Winner'] = 'unknown'

        data['Game Length(seconds)'] = str(result['frames'] / 16.)
        if not header_printed:
            print ",".join(data.keys())
            header_printed = True
        print ",".join(data.values())
    return header_printed



if __name__ == "__main__":
    debug = False
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
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk("replays"):
        path = root.split('/')
        for file in files:
            if file.endswith(".SC2Replay"):
                replay_files.append(root + "/" + file)
    #print replay_files
    error_replays = []

    for replay in replay_files:
        count += 1
        try:
            f = spawningtool.parser.parse_replay(replay)
            #print replay
            if debug:
                print "debug: number of players detected: ", len(f['players'])
            if len(f['players']) != 2:
                error_replays.append(replay)
                continue
            match_stats[classify_matchup(f)] += 1
            header_printed = print_results(f, header_printed)
        except (spawningtool.exception.ReadError, AttributeError, UnicodeEncodeError, KeyError, IndexError):
            #print replay
            error_replays.append(replay)
            continue
    print error_replays
    print match_stats
    print count
