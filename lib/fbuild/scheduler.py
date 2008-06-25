import sys
import threading
import queue

# -----------------------------------------------------------------------------

class Scheduler:
    def __init__(self, count=0, worker_timeout=1.0):
        self.__queue = queue.Queue()
        self.__threadcount_lock = threading.RLock()
        self.__threads = []
        self.__future_lock = threading.RLock()
        self.__worker_timeout = worker_timeout
        self.set_threadcount(count)

    def qsize(self):
        return self.__queue.qsize()

    def set_threadcount(self, count):
        # we subtract one thread because we'll use the main one as well
        count = max(0, count - 1)

        with self.__threadcount_lock:
            for i in range(len(self.__threads) - count):
                t = self.__threads.pop()
                t.stop()

            for i in range(count - len(self.__threads)):
                thread = WorkerThread(self.__queue, self.__worker_timeout)
                self.__threads.append(thread)
                thread.start()

    def get_threadcount(self):
        return len(self.__threads)

    threadcount = property(get_threadcount, set_threadcount)

    def future(self, function, *args, **kwargs):
        with self.__future_lock:
            f = Future(self.__queue, function, args, kwargs)
            self.__queue.put(f)

        return f

    def evaluate(self, future):
        # evaluate if it actually is a future
        while isinstance(future, Future):
            future = future()
        return future

    def join(self):
        with self.__future_lock:
            while _run_one(self.__queue, raise_exceptions=True, block=False):
                pass

            res = self.__queue.join()

            # check for any dead threads
            for thread in self.__threads:
                if thread._exc:
                    raise thread._exc

    def shutdown(self):
        self.set_threadcount(0)

    def __del__(self):
        # make sure we kill the threads
        self.shutdown()


def _run_one(q, raise_exceptions=False, *args, **kwargs):
    """
    Run one task. This is a separate function to break up a circular
    dependency.
    """
    try:
        f = q.get(*args, **kwargs)
    except queue.Empty:
        return False

    try:
        f.start(raise_exceptions=raise_exceptions)
        return True
    finally:
        q.task_done()

# -----------------------------------------------------------------------------

class WorkerThread(threading.Thread):
    def __init__(self, queue, timeout):
        super(WorkerThread, self).__init__()
        self.set_daemon(True)

        self.__queue = queue
        self.__timeout = timeout
        self.__finished = False
        self._exc = None

    def run(self):
        try:
            while not self.__finished:
                _run_one(self.__queue, timeout=self.__timeout)
        except Exception as e:
            self._exc = e

    def stop(self):
        self.__finished = True

# -----------------------------------------------------------------------------

class Future:
    def __init__(self, queue, function, args, kwargs):
        self.__queue = queue
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs
        self.__event = threading.Event()
        self.__result = None
        self.__exc = None

    def __call__(self):
        while not self.__event.is_set():
            # we're going to block anyway, so just run another future
            if not _run_one(self.__queue, block=False) and \
                    not self.__event.is_set():
                # there weren't any tasks for us and we're still waiting, so
                # just block until the task is done
                self.__event.wait()

        if self.__exc:
            raise self.__exc

        return self.__result

    def __repr__(self):
        return '<%s: %s, %s, %s>' % (
            self.__class__.__name__,
            self.__function.__name__,
            self.__args,
            self.__kwargs,
        )

    def start(self, raise_exceptions=False):
        try:
            self.__result = self.__function(*self.__args, **self.__kwargs)
        except Exception as e:
            if raise_exceptions:
                raise e
            else:
                self.__exc = e

        self.__event.set()
