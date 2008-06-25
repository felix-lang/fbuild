import time
import random
import unittest

import fbuild

# -----------------------------------------------------------------------------

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = fbuild.Scheduler(self.threads)

    def tearDown(self):
        self.scheduler.shutdown()
        self.scheduler = None

    def testSimple(self):
        i = 0
        def f():
            nonlocal i
            i += 1
            return i

        future = self.scheduler.future(f)
        self.assertEquals(future(), 1)
        self.assertEquals(future(), 1)

        future = self.scheduler.future(f)
        self.assertEquals(future(), 2)
        self.assertEquals(future(), 2)

    def testMultiple(self):
        def g(i):
            time.sleep(random.random() * .1)
            return i + 1

        fs = [self.scheduler.future(g, i) for i in range(10)]
        self.assertEquals([f() for f in fs], list(range(1, 11)))

    def run(self, *args, **kwargs):
        for i in range(10):
            self.threads = i
            super(TestScheduler, self).run(*args, **kwargs)

# -----------------------------------------------------------------------------

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestScheduler)

    return suite
