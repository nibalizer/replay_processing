import argparse
import errno
import logging
import os
import sys


def verbose_check(args):
    val = args.verbose or os.environ.get("SC2DEBUG")
    # setup the logging levels
    logger = logging.getLogger("replayParser")
    logger.setLevel(logging.DEBUG if val else logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return val, logger


def replay_check(args):
    if args.replay_folder:
        # Check to see if valid directory
        if os.path.isdir(args.replay_folder):
            return args.replay_folder, None
        else:
            return None, "Path given is not a directory. Exiting"
    else:
        env_replays = os.environ.get("SC2REPLAYS")
        if env_replays:
            # Check to see if valid directory
            if os.path.isdir(env_replays):
                return env_replays, None
            else:
                return None, "Path in SC2REPLAYS is not a directory. Exiting"
        else:
            return None, "Replays directory has not been given for neither --replay_folder nor environment variable SC2REPLAYS. Exiting"


def parse_params():
    args = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("-R", "--replay_folder", help="Path to directory we want to pull data from")
    parser.add_argument("-M", "--max_replays", help="Maximum number of replay files to parse", type=int)
    parser.add_argument("-T", "--worker_threads", help="Size of worker thread pool used in parsing files", default=5, type=int)
    parser.add_argument("-v", "--verbose", help="Print all output if set, else only critical logging", action="store_true")
    parser.add_argument("-d", "--debug", help="Enable debugging from application", action="store_true")
    parser.add_argument("-a", "--all_matches", help="Only take into account 1v1 matchups", action="store_true")
    parser.add_argument("-o", "--output_path", type=str,
                        help="Destination to output CSV. Default is stdout.")
    parser.add_argument("-t", "--tag-file", type=str)

    tmp = parser.parse_args()
    args["verbose"], args["logger"] = verbose_check(tmp)
    args["debug"] = tmp.debug
    args["all_matches"] = tmp.all_matches
    # Check for replay_folder
    replay_folder, err = replay_check(tmp)
    if replay_folder:
        args["replay_dir"] = replay_folder
    else:
        args["logger"].critical(err)
        exit(errno.EINVAL)

    for arg in ('max_replays', 'output_path', 'tag_file'):
        if hasattr(tmp, arg):
            args[arg] = getattr(tmp, arg)

    # default thread count is 5
    args["threads"] = tmp.worker_threads if tmp.worker_threads > 0 else 5

    return args
