
import subprocess, re, sys, logging

logger = logging.getLogger(__name__)

class PingWrapper():

    single_matcher = re.compile("(?P<bytes>\d+) bytes from (?P<IP>\d+.\d+.\d+.\d+): icmp_seq=(?P<sequence>\d+) ttl=(?P<ttl>\d+) time=(?P<time>\d+(.\d+)?) ms")
    # should match lines like this:
    # 64 bytes from 192.168.178.45: icmp_seq=2 ttl=64 time=103 ms
    end_matcher = re.compile("rtt min/avg/max/mdev = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)/(?P<mdev>\d+.\d+)")
    # should match lines like this:
    # rtt min/avg/max/mdev = 0.234/0.234/0.234/0.000 ms
    # alternative matcher for a different ping utility:
    #end_matcher = re.compile("round-trip min/avg/max/stddev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")

    def __init__(self, ping_command='ping -c4 -i 1 localhost'):
        self.ping_command = ping_command
        self.ping_process = None

    def run(self):
        self.ping_process = subprocess.Popen(
            self.ping_command,
            shell=True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )
        for line in iter(self.ping_process.stdout.readline, b""):
            line = line.decode('ascii').strip()
            if not line: continue
            logger.debug("Analyzing this line: " + line)
            match = self.single_matcher.match(line)
            if match:
                logger.debug("Matches found: {}".format(match.groups()))
                time = float(match.group('time'))
                yield time
                continue
            match = self.end_matcher.match(line)
            if match:
                logger.debug("Matches found: {}".format(match.groups()))
                continue
            logger.debug("Didn't understand this line: " + line)
        self.returncode = self.ping_process.wait()
