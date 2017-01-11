import os
import spawningtool.parser


def classify_matchup(result):
    #print result['players']
    races = []
    for player in result['players'].values():
        print('{} ({})'.format(player['name'], player['race']))
        races.append(player['race'])
    matchup = sorted(races)[0][0]
    matchup += "v"
    matchup += sorted(races)[1][0]
    print matchup
    return matchup


def write_builds(result):
    print "writing out build"
    matchup = classify_matchup(result)
    races = []
    for player in result['players'].values():
        races.append(player['race'])

    print "races:",races
    for player in result['players'].values():
        local_races = []
        for race in races:
            local_races.append(race)
        local_races.remove(player['race'])
        print "matchup is", player['race'], 'vs', local_races[0]
        print count
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
        for event in player['buildOrder']:
            if not event['is_worker']:
                if event['supply'] > 60:
                    break
                print('{} {} {}{}'.format(
                    event['supply'],
                    event['time'],
                    event['name'],
                    ' (Chronoboosted)' if event['is_chronoboosted'] else ''
                ))
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


def print_abilities(result):
    for player in result['players'].values():
        print('{} ({})'.format(player['name'], player['race']))
        for event in player['abilities']:
                print('{} {}'.format(
                    event['time'],
                    event['name'],
                ))
        print('')


def print_results(result):
    """
    Print the results of the build order
    """
    print(result['map'])
    print(result['build'])
    write_builds(result)
    #print_builds(result)
#    print_units_lost(result)
#    print_abilities(result)



if __name__ == "__main__":
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
    print replay_files
    error_replays = []

    for replay in replay_files:
        count += 1
        try:
            f = spawningtool.parser.parse_replay(replay)
            print replay
            match_stats[classify_matchup(f)] += 1
            print_results(f)
        except spawningtool.exception.ReadError:
            print replay
            error_replays.append(replay)
            continue
    print error_replays
    print match_stats
    print count
