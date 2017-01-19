army_units = ['Marine',
              'Marauder',
              'Reaper',
              'Ghost',
              'BattleHellion',
              'Hellion',
              'Hellbat',
              'WidowMine',
              'SiegeTank',
              'Cyclone',
              'Thor',
              'Viking',
              'VikingFighter',
              'VikingAssault',
              'Medivac',
              'Liberator',
              'Raven',
              'Banshee',
              'Battlecruiser',
              'Nuke',  # I guess
              'Zealot',
              'Stalker',
              'Sentry',
              'Adept',
              'MothershipCore',
              'HighTemplar',
              'DarkTemplar',
              'Immortal',
              'Disruptor',
              'Colossus',
              'Archon',
              'Observer',
              'WarpPrism',
              'Phoenix',
              'VoidRay',
              'Oracle',
              'Tempest',
              'Carrier',
              'Zergling',
              'Roach',
              'Hydralisk',
              'SwarmHost',
              'Infestor',
              'Ultralisk',
              'Mutalisk',
              'Corruptor',
              'Viper',
              'Baneling',
              'BroodLord',
              'Overseer', ]


def populate_build_data(player, debug):
    data = {}
    if debug and False:
        for event in player['buildOrder']:
            if not event['is_worker']:
                # from pdb import set_trace; set_trace()
                print('debug: {} {} {}{}'.format(
                    event['supply'],
                    event['time'],
                    event['name'],
                    ' (Chronoboosted)' if event['is_chronoboosted'] else ''
                ))

    data.update(first_army_unit(player, debug))

    return data


def first_army_unit(player, debug):
    data = {}
    if debug:
        print "debug: running first army unit"
        for event in player['buildOrder']:
            if not event['is_worker']:
                if event['name'] in army_units:
                    print "debug: First army unit found", event['name']
                    data['first_army_unit'] = event['name']
                    data['first_army_unit_supply'] = str(event['supply'])
                    data['first_army_unit_time'] = event['time']
                    break
    return data
