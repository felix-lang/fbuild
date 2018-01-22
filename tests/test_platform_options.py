#!/usr/bin/env python3

"""Test cases for the platform_options parsing."""

from test import support
import unittest

from fbuild.builders.platform import parse_platform_options


class PlatformOptionsTestCase(unittest.TestCase):
    def test_platform_options(self):
        platform_options = [
            ({'posix'}, {'flags+': ['-posix']}),
            ({'clang'}, {'flags+': ['-clang']}),
            ({'!clang'}, {'flags+': ['-notclang']}),
            ({'windows', '!clang'}, {'flags+': ['-wingcc']}),
            ({'windows', '!posix'}, {'flags+': ['-purewin']}),
        ]

        def check(platform, result):
            flags = []
            parse_platform_options(None, platform, platform_options, {'flags': flags})
            self.assertEqual(flags, result)

        check({'posix'}, ['-posix', '-notclang'])
        check({'posix', 'clang'}, ['-posix', '-clang'])
        check({'posix', 'windows'}, ['-posix', '-notclang', '-wingcc'])
        check({'windows', 'clang'}, ['-clang', '-purewin'])

def suite(*args, **kwargs):
    return unittest.TestLoader().loadTestsFromTestCase(PlatformOptionsTestCase)

if __name__ == "__main__":
    unittest.main()
