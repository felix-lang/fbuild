import fbuild
import fbuild.builders
from fbuild import ConfigFailed, execute
from fbuild.path import Path

# -----------------------------------------------------------------------------

class Linker:
    def __init__(self, ar, ranlib, flags, *, prefix, suffix):
        self.ar = ar
        self.ranlib = ranlib
        self.flags = flags
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, dst, srcs, *,
            libs=[],
            flags=[],
            ranlib_flags=[],
            destdir=None,
            buildroot=fbuild.buildroot,
            **kwargs):
        dst = Path(dst)
        dst = buildroot / dst.parent / self.prefix + dst.name + self.suffix
        srcs = Path.glob_all(srcs)

        assert srcs, 'no sources passed into ar'

        # exit early if not dirty
        if not dst.is_dirty(srcs, libs):
            return dst

        if destdir is not None:
            destdir.make_dirs()
            dst = destdir / dst

        cmd = [self.ar]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)
        cmd.extend(libs)

        execute(cmd,
            msg1=self.ar,
            msg2='%s -> %s' % (' '.join(srcs), dst),
            color='cyan',
            **kwargs)

        if self.ranlib is not None:
            cmd = [self.ranlib]
            cmd.extend(ranlib_flags)
            cmd.append(dst)

            execute(cmd,
                msg1=self.ranlib,
                msg2=dst,
                color='cyan',
                **kwargs)

        return dst

    def __str__(self):
        return ' '.join([self.ar] + self.flags)

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

# -----------------------------------------------------------------------------

def config(ar=None, ranlib=None, *,
        prefix='lib',
        suffix='.a',
        link_flags=['-rc'],
        **kwargs):
    ar = ar or fbuild.builders.find_program(['ar'])

    if not ar:
        raise ConfigFailed('cannot find ar')

    ranlib = ranlib or fbuild.builders.find_program(['ranlib'])

    return Linker(ar, ranlib, link_flags,
        prefix=prefix,
        suffix=suffix,
        **kwargs)
