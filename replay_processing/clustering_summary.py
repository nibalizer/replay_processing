import argparse
import json
import sys

from replay_processing import model

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("replay_dir",
                        help="Path to directory of replays by sha.",
                        type=str)
    parser.add_argument("csv_dir",
                        help="Path to directory of build csvs.",
                        type=str)
    parser.add_argument("clustering_dir",
                        help="Path to directory of clustering data.",
                        type=str)
    parser.add_argument("clustering_name",
                        help="Name of clustering sample",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    cluster_dir = model.ClusteringDataDir(args.clustering_dir)
    clustering = cluster_dir.clustering_data(args.clustering_name)
    labels = clustering.labels

    print("Created %d labeled clusters" % len(labels))

    label_lengths = [(x, len(y)) for x, y in labels.items()]
    for label, length in sorted(label_lengths,
                                key=lambda x: x[1],
                                reverse=True):
        print("Label %s with popularity %d:" % (label, length))
        
        build_affs = [(x, x.affinity) for x in labels[label].builds]
        for build, affinity in sorted(build_affs,
                                      key=lambda x: x[1],
                                      reverse=True):
            print("\tBuild %s player %s with affinity %f" % (build.map_id,
                                                             build.map_player,
                                                             affinity))
