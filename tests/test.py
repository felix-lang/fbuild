#!/usr/bin/env python3.0

import sys
import doctest
import unittest

sys.path.append('../lib')

import test_scheduler
import test_env

# -----------------------------------------------------------------------------

def main():
    suite = unittest.TestSuite()
    suite.addTest(test_scheduler.suite())
    suite.addTest(test_env.suite())

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    return 0

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
