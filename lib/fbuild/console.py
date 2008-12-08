import sys
import threading
import contextlib
import collections

import fbuild

# ------------------------------------------------------------------------------

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
        try:
            color = colorcodes[color]
        except KeyError:
            # we couldn't find the color so just ignore
            pass
        else:
            return '\x1b[01;%.2dm%s\x1b[0m' % (color, s)

    return s

# ------------------------------------------------------------------------------

class _ThreadStack(threading.local, collections.UserList):
    pass

# ------------------------------------------------------------------------------

class Log:
    def __init__(self, file=None, *,
            verbose=0,
            nocolor=False,
            show_threads=False):
        self.file = file
        self.verbose = verbose
        self.nocolor = nocolor
        self.show_threads = show_threads

        self.maxlen = 25
        self._lock = threading.RLock()
        self._thread_stack = _ThreadStack()

    @contextlib.contextmanager
    def log_from_thread(self):
        self._thread_stack.append([])

        try:
            yield
        finally:
            msgs = self._thread_stack.pop()
            with self._lock:
                for msg, kwargs in msgs:
                    self._write(msg, **kwargs)

    def write(self, msg, *, buffer=True, **kwargs):
        if not buffer or fbuild.scheduler.count == 1:
            with self._lock:
                self._write(msg, **kwargs)
        else:
            if buffer and self._thread_stack:
                self._thread_stack[-1].append((msg, kwargs))
            else:
                self._write(msg, **kwargs)

    def _write(self, msg, color=None, verbose=0):
        # make sure message is a string
        msg = str(msg)
        if self.file:
            self.file.write(msg)

        if verbose <= self.verbose:
            if not self.nocolor:
                msg = color_str(msg, color)
            sys.stdout.write(msg)
        self.flush()

    def flush(self):
        if self.file:
            self.file.flush()
        sys.stdout.flush()

    def log(self, msg, color=None, verbose=0):
        with self._lock:
            self.write(msg, verbose=verbose, color=color)
            self.write('\n', verbose=verbose)

    def check(self, msg, result=None, color=None, verbose=0):
        if self.show_threads:
            msg = '%-10s: %s' % (threading.current_thread().name, msg)

        d = len(msg)
        if d >= self.maxlen:
            self.maxlen = min(d + 1, 40)

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
