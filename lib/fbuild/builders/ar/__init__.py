from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.platform
from fbuild import ConfigFailed, execute
from fbuild.path import Path

# ------------------------------------------------------------------------------

class Ar(fbuild.db.PersistentObject):
    def __init__(self, exe='ar', *,
            platform=None,
            prefix=None,
            suffix=None,
            flags=['-rc'],
            libpaths=[],
            libs=[],
            external_libs=[],
            ranlib='ranlib',
            ranlib_flags=[]):
        self.exe = fbuild.builders.find_program([exe])
        try:
            self.ranlib = fbuild.builders.find_program([ranlib])
        except fbuild.ConfigFailed:
            self.ranlib = None

        self.prefix = prefix or \
            fbuild.builders.platform.static_lib_prefix(platform)
        self.suffix = suffix or \
            fbuild.builders.platform.static_lib_suffix(platform)
        self.libpaths = libpaths
        self.libs = libs
        self.external_libs = external_libs
        self.flags = flags
        self.ranlib_flags = ranlib_flags

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

        cmd = [self.exe]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)
        #cmd.extend(libs)
        #cmd.extend(self.external_libs)
        #cmd.extend(external_libs)

        execute(cmd,
            msg1=str(self),
            msg2='%s -> %s' % (' '.join(srcs), dst),
            color='cyan',
            **kwargs)

        if self.ranlib is not None:
            cmd = [self.ranlib]
            cmd.extend(self.ranlib_flags)
            cmd.extend(ranlib_flags)
            cmd.append(dst)

            execute(cmd,
                msg1=self.ranlib.name,
                msg2=dst,
                color='cyan',
                **kwargs)

        return dst

    def __str__(self):
        return ' '.join(chain((self.exe.name,), self.flags))
