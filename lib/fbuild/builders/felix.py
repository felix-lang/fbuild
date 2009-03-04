import sys
from functools import partial
from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.platform
import fbuild.db
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.temp import tempfile

# ------------------------------------------------------------------------------

class Flx:
    def __init__(self, exe, flags=[]):
        # we split exe in case extra arguments were specified in the name
        self.exe = fbuild.builders.find_program([exe])
        self.flags = flags

        if not self.check_flags([]):
            raise ConfigFailed('%s failed to compile an exe' % self)

    def __call__(self, src, *args,
            static=False,
            includes=[],
            flags=[],
            cwd=None,
            **kwargs):
        cmd = [self.exe]

        if sys.platform == 'win32':
            cmd.insert(0, 'c:\python26\python.exe')

        if static:
            cmd.append('--static')

        cmd.append('--output_dir=' + src.parent)
        cmd.extend('-I' + i for i in sorted(includes) if Path(i).exists())
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(src)

        return execute(cmd, *args, **kwargs)

    def check_flags(self, flags=[]):
        if flags:
            logger.check('checking %s with %s' %
                (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        with tempfile('', suffix='.flx') as src:
            try:
                self(src, flags=flags, quieter=1)
            except ExecutionError:
                logger.failed()
                return False

        logger.passed()
        return True

    def __str__(self):
        return ' '.join([self.exe] + self.flags)

    def __eq__(self, other):
        return isinstance(other, Flx) and \
            self.exe == other.exe

# ------------------------------------------------------------------------------

class Felix(fbuild.builders.AbstractCompiler):
    def __init__(self, exe='flx.py', *,
            platform=None,
            static=False,
            includes=[],
            flags=[]):
        super().__init__(src_suffix='.flx')

        self.flx = Flx(exe, flags=flags)
        self.exe_suffix = fbuild.builders.platform.exe_suffix(platform)
        self.lib_suffix = fbuild.builders.platform.shared_lib_suffix(platform)
        self.static = static
        self.includes = includes
        self.flags = flags

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, *args, **kwargs) -> fbuild.db.DST:
        """Compile a felix file and cache the results."""
        return self.uncached_compile(src, *args, **kwargs)

    def uncached_compile(self, src, *,
            static=None,
            includes=[],
            flags=[],
            buildroot=None,
            **kwargs):
        """Compile a felix file without caching the results.  This is needed
        when compiling temporary files."""
        buildroot = buildroot or fbuild.buildroot
        src_buildroot = src.addroot(buildroot)

        static = static or self.static

        if static:
            dst = src_buildroot.replaceext(self.exe_suffix)
        else:
            dst = src_buildroot.replaceext(self.lib_suffix)

        if src != src_buildroot:
            src_buildroot.parent.makedirs()
            src.copy(src_buildroot)
            src = src_buildroot

        includes = set(includes)
        includes.update(self.includes)

        cmd_flags = ['-c']
        cmd_flags.extend(self.flags)
        cmd_flags.extend(flags)

        self.flx(src, self.flx, '%s -> %s' % (src, dst),
            static=static,
            includes=includes,
            flags=cmd_flags,
            color='green',
            **kwargs)

        return dst

    def build_objects(self, srcs, **kwargs):
        return fbuild.scheduler.map(partial(self.compile, **kwargs), srcs)

    def run(self, src, *args, **kwargs):
        src = src.replaceexts({self.exe_suffix: '', self.lib_suffix: ''})
        return self.flx(src, *args, **kwargs)

    # --------------------------------------------------------------------------

    def tempfile_run(self, code='', *, quieter=1, **kwargs):
        with self.tempfile(code) as src:
            exe = self.uncached_compile(src, quieter=quieter, **ckwargs)
            return self.run(exe, quieter=quieter, **kwargs)

    # --------------------------------------------------------------------------

    def __eq__(self, other):
        return isinstance(other, Felix) and \
            self.exe == other.exe and \
            self.exe_suffix == other.exe_suffix
