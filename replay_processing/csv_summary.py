import argparse
import csv
import sys

from replay_processing import model

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("clustering_dir",
                        help="Path to directory of clustering data.",
                        type=str)
    parser.add_argument("clustering_name",
                        help="Name of clustering sample",
                        type=str)
    parser.add_argument("csv_dest",
                        help="Destination path for CSV.",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    cluster_dir = model.ClusteringDataDir(args.clustering_dir)
    clustering = cluster_dir.clustering_data(args.clustering_name)
    replays_info = cluster_dir.replays_info()

    with open(args.csv_dest, 'w') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(('replay_id', 'map_name', 'replay_time',
                             'player_id', 'build_tag'))
        for label_name, label in clustering.labels.items():
            for build in label.builds:
                replay = replays_info.replay(build.map_id)
                csv_writer.writerow((build.map_id, replay.map_name,
                                     replay.seconds, build.map_player,
                                     label.tag or -1))
