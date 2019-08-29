import sys, logging

logger = logging.getLogger(__name__)

def main():
    import argparse
    from pklaus.network.ping.ping_wrapper import PingWrapper
    parser = argparse.ArgumentParser(description='Ping a host and create histogram.')
    parser.add_argument('host', help='The host to ping')
    parser.add_argument('--count', '-c', type=int, default=4, help='Number of times the host should be pinged')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Interval between individual pings.')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output for this script')
    args = parser.parse_args()

    if args.debug: logging.basicConfig(format='%(levelname)s:%(message)s', level='DEBUG')

    ping_wrapper = PingWrapper(f'ping {args.host} -c{args.count} -i{args.interval}')
    try:
        for round_trip_time in ping_wrapper.run():
            print(round_trip_time)
            sys.stdout.flush()
    except KeyboardInterrupt:
        sys.exit()

    exit(ping_wrapper.returncode)
