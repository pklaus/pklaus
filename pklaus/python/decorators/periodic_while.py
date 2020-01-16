import time

def periodic_while(period=60, debug=False):
    def decorator(func):
        def call(*args, **kw):
            last_time = time.time()
            while True:
                func(*args, **kw)
                sleep_time = max(period - (time.time() - last_time), 0.0)
                if debug:
                    print('sleeping for {} s now.'.format(sleep_time))
                time.sleep(sleep_time)
                last_time = time.time()
        return call
    return decorator
