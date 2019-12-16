import subprocess, select, threading, time

class TailF():
    polling_timeout = 0.0005
    inter_polling_sleep = 0.005
    initial_tail_done_threshold = 10
    def __init__(self, filename, n=600, encoding=None):
        self.filename = filename
        self.n = n
        self._f = subprocess.Popen(['tail', '-n', str(n), '-F', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        self._p = select.poll()
        self._p.register(self._f.stdout.raw)
        self.lines = []
        self._new_line_event_callbacks = []
        self._initial_tail_done_callbacks = []
        self._subsequent_misses= 0
        self._initial_tail_done = False
        self._running = False
        self.encoding = encoding

    def register_new_line_event_callback(self, callback):
        self._new_line_event_callbacks.append(callback)

    def register_initial_tail_done_callback(self, callback):
        self._initial_tail_done_callbacks.append(callback)

    def _add_line(self, line):
        if self.encoding:
            line = line.decode(self.encoding)
        self.lines.append(line)
        if len(self.lines) > self.n:
            self.lines = self.lines[-500:]
        for callback in self._new_line_event_callbacks:
            callback(line)

    def start(self):
        # start / resume watching for new incoming lines
        self._running = True
        def worker():
            while self._running:
                if self._p.poll(self.polling_timeout):
                #if select.select([self._f.stdout.raw], [], [], self.polling_timeout)[0]:
                    line = self._f.stdout.raw.readline()
                    if line in ('', b''):
                        # empty string - EOF - stopping worker
                        break
                    self._add_line(line)
                    if not self._initial_tail_done:
                        self._subsequent_misses = 0
                else:
                    if not self._initial_tail_done:
                        if self._subsequent_misses >= self.initial_tail_done_threshold:
                            self._initial_tail_done = True
                            for callback in self._initial_tail_done_callbacks:
                                callback()
                        else:
                            self._subsequent_misses += 1
                    time.sleep(self.inter_polling_sleep)
        self._worker_thread = threading.Thread(target=worker, daemon=0)
        self._worker_thread.start()

    def pause(self):
        # pause watching for new incoming lines
        self._running = False
        self._worker_thread.join()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help="File to watch for new lines at the end (= 'tail -f' in Python)")
    args = parser.parse_args()

    ft = TailF(args.file)
    ft.encoding = 'utf-8'

    lines = []
    ft.register_new_line_event_callback(lambda line: lines.append(line))
    def start_reporting_new_lines():
        ft.register_new_line_event_callback(lambda line: print(f"{time.time():.4f} - new line '{line.strip()}'"))
    ft.register_initial_tail_done_callback(lambda: print(f"initial tail done. # of lines: {len(lines)}") or start_reporting_new_lines())

    print("Start watching for new lines...")
    ft.start()

    time.sleep(20)

    print("Pausing the watcher - incoming lines will be looked at once resumed...")
    ft.pause()
    time.sleep(20)

    print("Start watching for new lines...")
    ft.start()
    time.sleep(20)

    ft.pause()
    del ft
