
from multiprocessing import Process, Lock, Event, Pipe
import os, signal, logging

logger = logging.getLogger(__name__)

class TimelimitException(Exception):
    def __init__(self, sig):
        self.sig = sig

class Timelimit():

    """
    A class that can call a target and automatically
    kills it if it's still running after a specified
    amount of time.

    Modeled after the interface of the timelimit
    http://manpages.ubuntu.com/manpages/disco/en/man1/timelimit.1.html
    """

    killsig = signal.SIGKILL
    warnsig = signal.SIGTERM
    killtime = 120.
    warntime = 3600.

    def __init__(self, target, args=(), kwargs={}):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self._running = Lock()
        self._process = None
        self._result = None

    def run(self):
        self._running.acquire()
        recv_end, send_end = Pipe(False)
        def worker(send_end):
            pid = os.getpid()
            os.setpgid(pid, pid)
            result = self.target(*self.args, **self.kwargs)
            send_end.send(result)
        p = Process(target=worker, args=(send_end,))
        self._process = p
        p.start()
        p.join(timeout=self.warntime)
        if p.is_alive():
            logger.warning('sending warning signal %s', self.warnsig)
            #p.kill()
            #p.terminate()
            #os.kill(p.pid, self.warnsig)
            os.killpg(os.getpgid(p.pid), self.warnsig)
            # ^ see https://stackoverflow.com/a/48304304/183995
            p.join(timeout=self.killtime)
            if p.is_alive():
                logger.warning('sending kill signal %s', self.killsig)
                os.killpg(os.getpgid(p.pid), self.killsig)
                p.join()
                raise TimelimitException(self.killsig)
            else:
                raise TimelimitException(self.warnsig)
        else:
            self._result = recv_end.recv()
        self._running.release()

    def join(self):
        return self._process.join()

def main():
    import argparse, subprocess
    def signal_type(sig_str):
        def int_strategy(sig_str):
            return signal.Signals(int(sig_str))
        def str_strategy_1(sig_str):
            return signal.Signals[sig_str]
        def str_strategy_2(sig_str):
            return signal.Signals['SIG' + sig_str]
        for strategy in (int_strategy, str_strategy_1, str_strategy_2):
            try:
                return strategy(sig_str)
            except Exception as e:
                pass
        raise argparse.ArgumentTypeError(f"'{sig_str}' is not a valid signal number or signal name")
    parser = argparse.ArgumentParser()
    parser.add_argument('--propagate', '-p', action='store_true')
    parser.add_argument('--quiet', '-q', action='store_true')
    parser.add_argument('--killsig', '-S', default=signal.SIGKILL, type=signal_type)
    parser.add_argument('--warnsig', '-s', default=signal.SIGTERM, type=signal_type)
    parser.add_argument('--killtime', '-T', default=120., type=float)
    parser.add_argument('--warntime', '-t', default=3600., type=float)
    parser.add_argument('cmd')
    args = parser.parse_args()
    if args.propagate:
        raise NotImplementedError('--propagate flag')
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    tl = Timelimit(subprocess.run, args=(args.cmd,), kwargs=dict(shell=True, check=False))
    tl.killsig = args.killsig
    tl.warnsig = args.warnsig
    tl.killtime = args.killtime
    tl.warntime = args.warntime
    try:
        tl.run()
    except TimelimitException as te:
        return 128 + te.sig
    return tl._result.returncode
