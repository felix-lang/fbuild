#!/usr/bin/env python3.0

import sys
import doctest
import unittest

sys.path.append('../lib')

import test_functools
import test_scheduler

# -----------------------------------------------------------------------------

def main():
    suite = unittest.TestSuite()
    suite.addTest(test_functools.suite())
    suite.addTest(test_scheduler.suite())

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    return 0

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
