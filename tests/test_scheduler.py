#!/usr/bin/env python3.0

import time
import random
import unittest

from fbuild.sched import Scheduler

import threading

# -----------------------------------------------------------------------------

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.assertEquals(threading.active_count(), 1)

        self.scheduler = Scheduler(self.threads)

    def tearDown(self):
        # make sure we turn off all tht threads when shutting down
        del self.scheduler

        self.assertEquals(threading.active_count(), 1)

    def testMap(self):
        def f(x):
            time.sleep(random.random() * 0.01)
            return x + 1

        self.assertEquals(
            self.scheduler.map(f, [0,1,2,3,4,5,6,7,8,9]),
            [1,2,3,4,5,6,7,8,9,10])

        # now test if we can handle recursive scheduling
        def g(x):
            time.sleep(random.random() * 0.01)
            return self.scheduler.map(f, x)

        self.assertEquals(
            self.scheduler.map(g, [[0,1,2],[3,4,5],[6,7,8]]),
            [[1,2,3],[4,5,6],[7,8,9]])

    def run(self, *args, **kwargs):
        for i in range(10):
            self.threads = i
            super(TestScheduler, self).run(*args, **kwargs)

# -----------------------------------------------------------------------------

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestScheduler)

if __name__ == "__main__":
    unittest.main()
