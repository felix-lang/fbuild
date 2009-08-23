import sys

import fbuild
import fbuild.builders.text as text
import fbuild.path

# ------------------------------------------------------------------------------

def build(ctx):
    patterns = {'a': 1, 'b': 2}

    foo = text.format_substitute(ctx, 'foo.py', 'foo.py.in', patterns)
    ctx.execute((sys.executable, foo))

    bar = text.m4_substitute(ctx, 'bar.py', 'bar.py.in', patterns)
    ctx.execute((sys.executable, bar))
