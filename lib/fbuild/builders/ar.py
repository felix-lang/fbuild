from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.platform
from fbuild import ConfigFailed, execute
from fbuild.path import Path

# ------------------------------------------------------------------------------

class Ar(fbuild.db.PersistentObject):
    def __init__(self, ar=None, *,
            platform=None,
            prefix=None,
            suffix=None,
            flags=['-rc'],
            libpaths=[],
            libs=[],
            ranlib=None,
            ranlib_flags=[]):
        self.ar = fbuild.builders.find_program([ar or 'ar'])
        try:
            self.ranlib = fbuild.builders.find_program([ranlib or 'ranlib'])
        except fbuild.ConfigFailed:
            self.ranlib = None

        self.prefix = prefix or \
            fbuild.builders.platform.static_lib_prefix(platform)
        self.suffix = suffix or \
            fbuild.builders.platform.static_lib_suffix(platform)
        self.libpaths = tuple(libpaths)
        self.libs = tuple(libs)
        self.flags = tuple(flags)
        self.ranlib_flags = tuple(ranlib_flags)

    @fbuild.db.cachemethod
    def __call__(self, dst, srcs:fbuild.db.SRCS, *,
            libs:fbuild.db.SRCS=[],
            external_libs=[],
            flags=[],
            ranlib_flags=[],
            prefix=None,
            suffix=None,
            buildroot=None,
            **kwargs) -> fbuild.db.DST:
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
        dst.parent.makedirs()

        srcs = list(Path.globall(srcs))

        cmd = [self.ar]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)
        #cmd.extend(libs)
        #cmd.extend(external_libs)

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
