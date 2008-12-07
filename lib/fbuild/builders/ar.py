from itertools import chain

import fbuild
import fbuild.builders
from fbuild import ConfigFailed, execute
from fbuild.path import Path

# ------------------------------------------------------------------------------

class Linker:
    def __init__(self, ar, ranlib, flags=(), *, prefix, suffix,
            libpaths=(),
            libs=(),
            ranlib_flags=()):
        self.ar = ar
        self.ranlib = ranlib
        self.prefix = prefix
        self.suffix = suffix
        self.libpaths = tuple(libpaths)
        self.libs = tuple(libs)
        self.flags = tuple(flags)
        self.ranlib_flags = tuple(ranlib_flags)

    def __call__(self, dst, srcs, *,
            libs=(),
            flags=(),
            ranlib_flags=(),
            prefix=None,
            suffix=None,
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        #libs = set(libs)
        #libs.update(self.libs)
        #libs = sorted(libs)

        #assert srcs or libs, 'no sources passed into ar'
        assert srcs, 'no sources passed into ar'

        prefix = prefix or self.prefix
        suffix = suffix or self.suffix
        dst = Path(dst).addroot(buildroot)
        dst = dst.parent / prefix + dst.name + suffix
        srcs = list(Path.globall(srcs))

        # exit early if not dirty
        if not dst.isdirty(srcs, libs):
            return dst

        dst.parent.makedirs()

        cmd = [self.ar]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)
        #cmd.extend(libs)

        execute(cmd,
            msg1=self.ar,
            msg2='%s -> %s' % (' '.join(srcs), dst),
            color='cyan',
            **kwargs)

        if self.ranlib is not None:
            cmd = [self.ranlib]
            cmd.extend(self.ranlib_flags)
            cmd.extend(ranlib_flags)
            cmd.append(dst)

            execute(cmd,
                msg1=self.ranlib,
                msg2=dst,
                color='cyan',
                **kwargs)

        return dst

    def __str__(self):
        return ' '.join(chain((self.ar,), self.flags))

    def __repr__(self):
        return '%s(%r, ranlib=%r, flags=%r, prefix=%r, suffix=%r)' % (
            self.__class__.__name__,
            self.ar,
            self.ranlib,
            self.flags,
            self.prefix,
            self.suffix)

    def __eq__(self, other):
        return isinstance(other, Linker) and \
            self.ar == other.ar and \
            self.ranlib == other.ranlib and \
            self.flags == other.flags and \
            self.prefix == other.prefix and \
            self.suffix == other.suffix

    def __hash__(self):
        return hash((
            self.ar,
            self.ranlib,
            self.prefix,
            self.suffix,
            self.libpaths,
            self.libs,
            self.flags,
            self.ranlib_flags,
        ))

# ------------------------------------------------------------------------------

def config(ar=None, ranlib=None, *,
        prefix='lib',
        suffix='.a',
        flags=['-rc'],
        **kwargs):
    ar = ar or fbuild.builders.find_program(['ar'])

    if not ar:
        raise ConfigFailed('cannot find ar')

    ranlib = ranlib or fbuild.builders.find_program(['ranlib'])

    return Linker(ar, ranlib, flags,
        prefix=prefix,
        suffix=suffix,
        **kwargs)
