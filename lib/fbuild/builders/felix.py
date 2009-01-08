from functools import partial

import fbuild
import fbuild.db
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.temp import tempfile
from fbuild.builders import AbstractCompiler, find_program

# ------------------------------------------------------------------------------

class Flx:
    def __init__(self, exe, flags=[]):
        # we split exe in case extra arguments were specified in the name
        self.exe, *self.flags = str.split(exe)
        self.exe = Path(self.exe)
        self.flags.extend(flags)

    def __call__(self, src, *args,
            static=False,
            includes=[],
            flags=[],
            cwd=None,
            **kwargs):
        cmd = [self.exe]

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

@fbuild.db.caches
def config_flx(exe=None, default_exes=['flx'], *, flags=[]):
    exe = exe or find_program(default_exes)

    if not exe:
        raise MissingProgram('exe')

    flx = Flx(exe, flags)

    if not flx.check_flags([]):
        raise ConfigFailed('flx failed to compile an exe')

    return flx

# ------------------------------------------------------------------------------

class Felix(AbstractCompiler):
    def __init__(self, flx, *, exe_suffix, lib_suffix,
            static=False,
            includes=[],
            flags=[]):
        super().__init__(src_suffix='.flx')

        self.flx = flx
        self.exe_suffix = exe_suffix
        self.lib_suffix = lib_suffix
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

# ------------------------------------------------------------------------------

def config(exe=None, *,
        flags=[],
        exe_suffix='',
        lib_suffix='.dylib',
        **kwargs):
    flx = config_flx(exe, flags=flags)

    return Felix(flx, exe_suffix=exe_suffix, lib_suffix=lib_suffix)
