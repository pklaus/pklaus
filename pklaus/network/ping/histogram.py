import sys, logging

logger = logging.getLogger(__name__)

def main():
    import argparse
    from pklaus.network.ping import ping
    parser = argparse.ArgumentParser(description='Ping a host and create histogram.')
    parser.add_argument('host', help='The host to ping')
    parser.add_argument('--count', '-c', type=int, default=4, help='Number of times the host should be pinged')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Interval between individual pings.')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output for this script')
    args = parser.parse_args()

    if args.debug: logging.basicConfig(format='%(levelname)s:%(message)s', level='DEBUG')

    try:
        retcode = ping(host=args.host, count=args.count, interval=args.interval, debug=args.debug)
    except KeyboardInterrupt:
        sys.exit()

    exit(retcode)
