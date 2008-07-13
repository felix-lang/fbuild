import time
import random
import unittest

from fbuild.scheduler import Scheduler

# -----------------------------------------------------------------------------

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler(self.threads)

    def tearDown(self):
        self.scheduler.shutdown()
        self.scheduler = None

    def testMap(self):
        def f(x):
            time.sleep(random.random() * 0.1)
            return x + 1

        self.assertEquals(
            self.scheduler.map(f, [0,1,2,3,4,5,6,7,8,9]),
            [1,2,3,4,5,6,7,8,9,10])

    def run(self, *args, **kwargs):
        for i in range(10):
            self.threads = i
            super(TestScheduler, self).run(*args, **kwargs)

# -----------------------------------------------------------------------------

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestScheduler)

    return suite
