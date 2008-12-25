import pprint
import random
import os

import fbuild
import fbuild.db
from fbuild.path import Path

# ------------------------------------------------------------------------------

@fbuild.db.caches
def foo(src:fbuild.db.SRC, dst, *, buildroot=None) -> fbuild.db.DST:
    dst = Path.addroot(dst, buildroot or fbuild.buildroot)

    fbuild.logger.log(' * foo: %s %s' % (src, dst), color='cyan')

    with open(src) as f:
        x = f.read().strip()

    with open(dst, 'w') as f:
        print(src, dst, x, file=f)

    return dst

# ------------------------------------------------------------------------------

class Builder:
    def __init__(self, prefix, suffix):
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, src, dst, *, buildroot=None):
        buildroot = buildroot or fbuild.buildroot
        dst = Path.addroot(dst, buildroot).addprefix(self.prefix) + self.suffix

        fbuild.logger.log(' * Builder.__call__: %s %s' % (src, dst),
            color='cyan')

        with open(src) as f:
            x = f.read().strip()

        with open(dst, 'w') as f:
            print(src, dst, x, file=f)

        return dst

    def __hash__(self):
        return hash((self.prefix, self.suffix))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.prefix == other.prefix and \
            self.suffix == other.suffix

class C(fbuild.db.PersistentObject):
    def __init__(self, builder):
        self.builder = builder

    @fbuild.db.cachemethod
    def bar(self, src:fbuild.db.SRC, dst, *, buildroot=None) -> fbuild.db.DST:
        return self.builder(src, dst)

# ------------------------------------------------------------------------------

def build():
    print('calling cached functions')
    print(foo('foo', 'foo1'))
    print(foo('foo', 'foo2'))
    print(foo('foo', 'foo1'))

    print()
    print('calling cached methods')
    builder = Builder('prefix', '.suffix')
    c = C(builder)
    print(c.bar('foo', 'bar1'))
    print(c.bar('foo', 'bar2'))
    print(c.bar('foo', 'bar1'))

    print()
    print('calling cached methods on a new instance')
    c = C(builder)
    print(c.bar('foo', 'bar1'))
    print(c.bar('foo', 'bar2'))
