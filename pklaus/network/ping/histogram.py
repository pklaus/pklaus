import logging

logger = logging.getLogger(__name__)

def main():
    import argparse, sys, math
    import plotille
    import reprint
    from pklaus.network.ping.ping_wrapper import PingWrapper
    parser = argparse.ArgumentParser(description='Ping a host and create histogram.')
    parser.add_argument('host', help='The host to ping')
    parser.add_argument('--count', '-c', type=int, default=60, help='Number of times the host should be pinged')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Interval between individual pings.')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output for this script')
    args = parser.parse_args()

    if args.debug: logging.basicConfig(format='%(levelname)s:%(message)s', level='DEBUG')

    ping_wrapper = PingWrapper(f'ping {args.host} -c{args.count} -i{args.interval}')
    try:
        round_trip_times = []
        with reprint.output(initial_len=24, interval=0) as output_lines:
            for round_trip_time in ping_wrapper.run():
                round_trip_times.append(round_trip_time)
                if len(round_trip_times) < 2: continue
                x_min = math.floor(min(round_trip_times))
                x_max = math.ceil(max(round_trip_times))
                hist_string = plotille.histogram(round_trip_times, width=60,
                                                 height=20, x_min=x_min, x_max=x_max)
                output_lines.change(hist_string.split('\n'))
    except KeyboardInterrupt:
        sys.exit()

    exit(ping_wrapper.returncode)
