import sys
import threading

# -----------------------------------------------------------------------------

colorcodes = {
    'black'  : 30,
    'red'    : 31,
    'green'  : 32,
    'yellow' : 33,
    'blue'   : 34,
    'magenta': 35,
    'cyan'   : 36,
    'white'  : 37,
}

def color_str(s, color):
    if color is not None and sys.platform != 'win32':
        return '\x1b[01;%.2dm%s\x1b[0m' % (colorcodes[color], s)
    else:
        return s

# -----------------------------------------------------------------------------

class Log:
    def __init__(self, filename='fbuild.log', *,
            verbose=0,
            nocolor=False,
            show_threads=False):
        self.logfile = open(filename, 'w')
        self.verbose = verbose
        self.nocolor = nocolor
        self.show_threads = show_threads

        self.maxlen = 25
        self._lock = threading.RLock()
        self._thread_stacks = {}

    def push_thread(self):
        stack = self._thread_stacks.setdefault(threading.current_thread(), [])
        stack.append([])

    def pop_thread(self):
        msgs = self._thread_stacks[threading.current_thread()].pop()

        with self._lock:
            for msg, kwargs in msgs:
                self._write(msg, **kwargs)

    def write(self, msg, *, buffer=True, **kwargs):
        if not buffer:
            with self._lock:
                self._write(msg, **kwargs)
        else:
            stack = self._thread_stacks.setdefault(
                threading.current_thread(), [])

            if buffer and stack:
                stack[-1].append((msg, kwargs))
            else:
                self._write(msg, **kwargs)

    def _write(self, msg, color=None, verbose=0):
        # make sure message is a string
        msg = str(msg)
        self.logfile.write(msg)

        if verbose <= self.verbose:
            if not self.nocolor:
                msg = color_str(msg, color)
            sys.stdout.write(msg)
        self.flush()

    def flush(self):
        self.logfile.flush()
        sys.stdout.flush()

    def log(self, msg, color=None, verbose=0):
        self.write(msg, verbose=verbose, color=color)
        self.write('\n', verbose=verbose)

    def check(self, msg, result=None, color=None, verbose=0):
        import fbuild
        if self.show_threads and fbuild.scheduler.threadcount > 0:
            msg = '%-10s: %s' % (
                threading.current_thread().get_name(),
                msg,
            )

        d = len(msg)
        if d >= self.maxlen:
            self.maxlen = d + 1

        msg = msg.ljust(self.maxlen) + ': '

        if result is None:
            self.write(msg, color=color, verbose=verbose)
            self.write('\n', verbose=verbose + 1)
        else:
            self.write(msg, verbose=verbose)
            self.write(result, color=color, verbose=verbose)
            self.write('\n', verbose=verbose)

    def passed(self, msg='ok', color='green'):
        self.log(msg, color=color)

    def failed(self, msg='failed', color='yellow'):
        self.log(msg, color=color)
