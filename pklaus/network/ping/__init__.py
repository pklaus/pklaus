import subprocess, re, sys, logging

logger = logging.getLogger(__name__)

single_matcher = re.compile("(?P<bytes>\d+) bytes from (?P<IP>\d+.\d+.\d+.\d+): icmp_seq=(?P<sequence>\d+) ttl=(?P<ttl>\d+) time=(?P<time>\d+(.\d+)?) ms")
# should match lines like this:
# 64 bytes from 192.168.178.45: icmp_seq=2 ttl=64 time=103 ms
end_matcher = re.compile("rtt min/avg/max/mdev = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)/(?P<mdev>\d+.\d+)")
# should match lines like this:
# rtt min/avg/max/mdev = 0.234/0.234/0.234/0.000 ms
# alternative matcher for a different ping utility:
#end_matcher = re.compile("round-trip min/avg/max/stddev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")

def ping(host=None, count=4, interval=1.0, debug=False):
    pp = subprocess.Popen(
        ["ping", "-c", str(count), "-i", str(interval), host],
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT
    )

    round_trip_times = []
    for line in iter(pp.stdout.readline, b""):
        line = line.decode('ascii').strip()
        if not line: continue
        if debug: logger.debug("Analyzing this line: " + line)
        match = single_matcher.match(line)
        if match:
            if debug: logger.debug("Matches found: {}".format(match.groups()))
            time = float(match.group('time'))
            round_trip_times.append(time)
            print(time)
            sys.stdout.flush()
            continue
        match = end_matcher.match(line)
        if match:
            if debug: logger.debug("Matches found: {}".format(match.groups()))
            continue
        if debug: logger.debug("Didn't understand this line: " + line)
    return pp.wait()
