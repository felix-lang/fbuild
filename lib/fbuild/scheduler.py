import sys
import threading
import queue
import operator

# -----------------------------------------------------------------------------

class Scheduler:
    def __init__(self, count=0):
        self.__ready_queue = queue.Queue()
        self.__done_queue = queue.Queue()
        self.__threads = []

        for i in range(max(1, count)):
            thread = WorkerThread(self.__ready_queue)
            self.__threads.append(thread)
            thread.start()

    def map(self, function, srcs):
        '''
        Run the function over the input sources concurrently. This function
        returns the results in their initial order.
        '''

        nodes = (Node(function, src, index) for index, src in enumerate(srcs))
        nodes = sorted(self._evaluate(nodes), key=operator.attrgetter('index'))

        return [n.result for n in nodes]

    def map_with_dependencies(self, depends, function, srcs):
        '''
        Calculate the dependencies between the input sources and run them
        concurrently. This function returns the results in the order that they
        finished, not their initial order.
        '''

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
        results = []

        for task in tasks:
            for dep in task.dependencies:
                children.setdefault(dep, []).append(task)

            if task.can_run():
                count += 1
                task.running = True
                self.__ready_queue.put(task)

        while count != 0:
            task = self.__done_queue.get()
            count -= 1
            task.done = True
            if task.exc is not None:
                raise task.exc
            results.append(task)

            for child in children.get(task, []):
                if child.can_run():
                    count += 1
                    child.running = True
                    self.__ready_queue.put(child)

        return results

    def __del__(self):
        # make sure we kill the threads
        for thread in self.__threads:
            self.__ready_queue.put(None)

        for thread in self.__threads:
            thread.join()

# -----------------------------------------------------------------------------

class WorkerThread(threading.Thread):
    def __init__(self, ready_queue, done_queue):
        super().__init__()
        self.set_daemon(True)

        self.__ready_queue = ready_queue
        self.__done_queue = done_queue
        self.__finished = False

    def run(self):
        from fbuild import logger

        while True:
            task = self.__ready_queue.get()
            if task is None:
                break

            with logger.log_from_thread():
                try:
                    task.result = task.function(task.src)
                except Exception as e:
                    task.exc = e
                finally:
                    self.__ready_queue.task_done()
                    self.__done_queue.put(task)


# -----------------------------------------------------------------------------

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
