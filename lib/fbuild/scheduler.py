import sys
import threading
import Queue

# -----------------------------------------------------------------------------

class Scheduler:
    def __init__(self, maxsize, worker_timeout=1.0):
        self.__queue = Queue.Queue()

        # we subtract one thread because we'll use the main one as well
        self.threads = []
        for i in range(maxsize - 1):
            thread = WorkerThread(self.__queue, worker_timeout)
            self.threads.append(thread)
            thread.start()

    def qsize(self):
        return self.__queue.qsize()

    def future(self, function, *args, **kwargs):
        f = Future(self.__queue, function, args, kwargs)
        self.__queue.put(f)

        return f

    def join(self):
        while _run_one(self.__queue, raise_exceptions=True, block=False):
            pass

        return self.__queue.join()

    def shutdown(self):
        for thread in self.threads:
            thread.cancel()

    def __del__(self):
        # make sure we kill the threads
        self.shutdown()


def _run_one(queue, raise_exceptions=False, *args, **kwargs):
    """
    Run one task. This is a separate function to break up a circular
    dependency.
    """

    try:
        f = queue.get(*args, **kwargs)
    except Queue.Empty:
        return False

    try:
        f.start(raise_exceptions=raise_exceptions)
        return True
    finally:
        queue.task_done()

# -----------------------------------------------------------------------------

class WorkerThread(threading.Thread):
    def __init__(self, queue, timeout):
        super(WorkerThread, self).__init__()
        self.setDaemon(True)

        self.__queue = queue
        self.__timeout = timeout
        self.__finished = False

    def run(self):
        while not self.__finished:
            _run_one(self.__queue, timeout=self.__timeout)

    def cancel(self):
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
        while not self.__event.isSet():
            # we're going to block anyway, so just run another future
            if not _run_one(self.__queue, block=False) and \
                    not self.__event.isSet():
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

def evaluate(future):
    # evaluate if it actually is a future
    if isinstance(future, Future):
        return future()
    return future
