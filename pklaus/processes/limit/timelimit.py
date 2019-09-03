
def main():
    import argparse, subprocess, logging
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', '-t', default=60., type=float)
    parser.add_argument('cmd')
    args = parser.parse_args()
    
    try:
        result = subprocess.run(args.cmd, timeout=args.timeout, shell=True, check=False)
    except subprocess.TimeoutExpired:
        logger.warning('process was running for too long, had to be killed...')
        return 255
    return result.returncode
