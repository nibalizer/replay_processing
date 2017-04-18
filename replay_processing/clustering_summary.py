import argparse
import csv
import json
import os
import sys

from replay_processing import model, build_order_clustering

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("clustering_dir",
                        help="Path to directory of clustering data.",
                        type=str)
    parser.add_argument("clustering_name",
                        help="Name of clustering sample",
                        type=str)
    parser.add_argument("--json-output",
                        help="Dest of map,player: tag output",
                        type=str)
    parser.add_argument("--update-csv",
                        help="Dest of replayscan csv to update.",
                        type=str)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    cluster_dir = model.ClusteringDataDir(args.clustering_dir)
    replays_info = cluster_dir.replays_info

    all_clusterings = cluster_dir.all_clustering_data()
    tag_votes = {}
    for clustering in all_clusterings:
        for label_name, label in clustering.labels.items():
            if label.tag is not None:
                for build in label.builds:
                    votes = tag_votes.get((build.map_id, build.map_player), [])
                    votes.append((label.tag, clustering.confidence,
                                  build.affinity))
                    tag_votes[(build.map_id, build.map_player)] = votes

    clustering = cluster_dir.clustering_data(args.clustering_name)
    labels = clustering.labels

    print("Created %d labeled clusters" % len(labels))

    label_lengths = [(x, len(y)) for x, y in labels.items()]

    build_votes = {}
    for label_name, length in sorted(label_lengths,
                                key=lambda x: x[1],
                                reverse=True):
        label = labels[label_name]
        print("Label %s with popularity %d:" % (label_name, length))
        print("Label description: %s" % label.description)
        center_build = label.center
        print("Center Build: %s player %d" % (center_build.map_id,
                                              center_build.map_player))
        
        build_affs = [(x, x.affinity) for x in label.builds]
        unit_counts = {}
        for build, affinity in sorted(build_affs,
                                      key=lambda x: x[1],
                                      reverse=True):
            tag_confidence = {}
            votes = tag_votes.get((build.map_id, build.map_player))
            if votes:
                for tag, _confidence, _affinity in votes:
                    tag_confidence[tag] = _confidence * _affinity
                max_conf = None
                for tag, confidence in tag_confidence.items():
                    if max_conf is None:
                        max_conf = (tag, confidence)
                    elif max_conf[1] >= confidence:
                        max_conf = (tag, confidence)
                tag_str = tag
            else:
                tag_str = "Unknown"

            build_votes['%d@%s' % (build.map_player, build.map_id)] = tag_str

            print("\tBuild %s player %s with affinity %f Tag: %s" % (
                build.map_id,
                build.map_player,
                affinity,
                tag_str))

            player_build = build_order_clustering.PlayerBuild(
                0, build.map_id, build.map_player-1)
            player_build.load_events_file(build.events_path, 420)
            for unit, popularity in player_build.unit_counts.items():
                cur_unit_counts = unit_counts.get(unit, [])
                cur_unit_counts.append(popularity)
                unit_counts[unit] = cur_unit_counts

        unit_medians = {}
        for unit, counts in unit_counts.items():
            median = list(sorted(counts))[int(len(counts) / 2)]
            unit_medians[unit] = median
        print("Unit counts:")
        for unit, median in sorted(unit_medians.items(), key=lambda x: x[1],
                                   reverse=True):
            print("\t%s: %d" % (unit, median))

    if args.json_output:
        with open(args.json_output, 'w') as fh:
            json.dump(build_votes, fh)

    if args.update_csv:
        with open(args.update_csv + '.updated', 'w') as out_fh:
            csvwriter = csv.writer(out_fh, delimiter=',',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)
            with open(args.update_csv, 'r') as in_fh:
                csvreader = csv.reader(in_fh, delimiter=',', quotechar='|')
                lead_row = next(csvreader)
                lead_row.append('Build Order')
                csvwriter.writerow(lead_row)
                for row in csvreader:
                    filename = row[-1]
                    hash_ = os.path.basename(filename).split('.')[0]
                    try:
                        replay_info = replays_info.replay(hash_)
                    except Exception:
                        votes_str = 'Unknown'
                    else:
                        replay_players = [x.split('-')[1].strip().split(' ')[0] for x in replay_info.players]
                        player = row[8]
                        player_id = -1
                        if replay_players[0] == player:
                            player_id = 1
                        elif replay_players[1] == player:
                            player_id = 2
                        if player_id != -1:
                            key = '%d@%s' % (player_id, hash_)
                            try:
                                votes_str = build_votes[key]
                            except KeyError:
                                votes_str = 'Unknown'
                        else:
                            votes_str = 'Unknown'
                    row.append(votes_str)
                    csvwriter.writerow(row)
