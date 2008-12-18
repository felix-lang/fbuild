import sys

import fbuild
import fbuild.builders.text as text
import fbuild.path

# ------------------------------------------------------------------------------

def build():
    patterns = {'a': 1, 'b': 2}

    foo = text.format_substitute('foo.py', 'foo.py.in', patterns)
    fbuild.execute((sys.executable, foo))

    bar = text.m4_substitute('bar.py', 'bar.py.in', patterns)
    fbuild.execute((sys.executable, bar))
