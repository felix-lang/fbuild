import operator
import queue
import sys
import threading

# ------------------------------------------------------------------------------

class Scheduler:
    def __init__(self, count=0):
        self.__count = max(1, count)
        self.__ready_queue = queue.LifoQueue()
        self.__threads = []

        for i in range(self.__count):
            thread = WorkerThread(self.__ready_queue)
            self.__threads.append(thread)
            thread.start()

    @property
    def count(self):
        return self.__count

    def map(self, function, srcs):
        """Run the function over the input sources concurrently. This function
        returns the results in their initial order."""
        nodes = (Node(function, src, index) for index, src in enumerate(srcs))
        nodes = sorted(self._evaluate(nodes), key=operator.attrgetter('index'))

        return [n.result for n in nodes]

    def map_with_dependencies(self, depends, function, srcs):
        """Calculate the dependencies between the input sources and run them
        concurrently. This function returns the results in the order that they
        finished, not their initial order."""
        nodes = {}

        for src in srcs:
            nodes[src] = Node(function, src)

        for dep_node in self._evaluate([Node(depends, src) for src in srcs]):
            try:
                node = nodes[dep_node.src]
            except KeyError:
                # ignore missing dependencies
                pass
            else:
                for dep in dep_node.result:
                    try:
                        node.dependencies.append(nodes[dep])
                    except KeyError:
                        # ignore missing dependencies
                        pass

        return [n.result for n in self._evaluate(nodes.values())]

    def _evaluate(self, tasks):
        count = 0
        children = {}
        done_queue = queue.Queue()
        results = []

        for task in tasks:
            for dep in task.dependencies:
                children.setdefault(dep, []).append(task)

            if task.can_run():
                count += 1
                task.running = True
                self.__ready_queue.put((done_queue, task))

        current_thread = threading.current_thread()

        while count != 0:
            if isinstance(current_thread, WorkerThread):
                # we're inside an already running thread, so we're going to run
                # until all of our tasks are done
                try:
                    current_thread.run_one(block=False)
                except queue.Empty:
                    pass

                # see if any of our tasks are done yet
                try:
                    task = done_queue.get(block=False)
                except queue.Empty:
                    # no tasks done, so loop
                    continue
            else:
                # Unfortunately, We need a busy loop to give KeyboardInterrupt
                # a chance to get raised.
                while True:
                    try:
                        task = done_queue.get(block=False, timeout=1.0)
                    except queue.Empty:
                        pass
                    else:
                        break

            count -= 1
            task.done = True
            if task.exc is not None:
                # Clear our queue of tasks.
                for t in tasks:
                    t.done = True

                raise task.exc
            results.append(task)

            for child in children.get(task, []):
                if child.can_run():
                    count += 1
                    child.running = True
                    self.__ready_queue.put((done_queue, child))

        return results

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        # make sure we wake the threads before we kill them.
        for thread in self.__threads:
            self.__ready_queue.put(None)

        for thread in self.__threads:
            thread.shutdown()
            thread.join()

# ------------------------------------------------------------------------------

class WorkerThread(threading.Thread):
    def __init__(self, ready_queue):
        super().__init__()
        self.daemon = True

        self.__ready_queue = ready_queue
        self.__finished = False

    def shutdown(self):
        self.__finished = True

    def run(self):
        from fbuild import logger

        while not self.__finished:
            with logger.log_from_thread():
                if self.run_one():
                    break

    def run_one(self, *args, **kwargs):
        queue_task = self.__ready_queue.get(*args, **kwargs)

        try:
            # This should be tested in the try block so that we update the done
            # counter in the ready queue, even if we errored out.
            if queue_task is None:
                return True

            done_queue, task = queue_task
            try:
                task.run()
            finally:
                done_queue.put(task)
        finally:
            self.__ready_queue.task_done()

# ------------------------------------------------------------------------------

class Node:
    def __init__(self, function, src, index=None):
        self.function = function
        self.src = src
        self.index = index
        self.running = False
        self.done = False
        self.dependencies = []
        self.exc =None

    def can_run(self):
        if self.running or self.done:
            return False

        if not self.dependencies:
            return True

        return all(d.done for d in self.dependencies)

    def run(self):
        try:
            self.result = self.function(self.src)
        except Exception as e:
            self.exc = e
