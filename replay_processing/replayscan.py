
from parseargs import parse_params
from sc2files import parse_replays


def main():
    # Get params and environment variables
    params = parse_params()
    logger = params["logger"]
    # Parse replays using params
    logger.info("Parsing Replay Files")
    match_data, count, errors, error_replays, match_stats, korean_replays = parse_replays(params["replay_dir"],
                                                                                          params["threads"],
                                                                                          max_replays=params["max_replays"],
                                                                                          logger=logger)

    logger.info("Match Stats: {0}".format({k: v for k, v in match_stats.items()}))
    logger.info("Total Replays: {0}".format(count))
    logger.info("Error Replays: {0}".format(errors))
    logger.info("Error Percent: {0}".format(str(errors / float(count))))
    logger.info("Error Replays: \n  {0}".format(error_replays))
    logger.info("Korean replays: \n  {0}".format(korean_replays))


if __name__ == "__main__":
    main()
