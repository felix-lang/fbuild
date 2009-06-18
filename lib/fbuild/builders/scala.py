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

class Scalac:
    def __init__(self, exe, *,
            classpaths=[],
            sourcepaths=[],
            debug=False,
            optimize=False,
            target=None,
            flags=[]):
        # we split exe in case extra arguments were specified in the name
        self.exe = fbuild.builders.find_program([exe])
        self.classpaths = classpaths
        self.sourcepaths = sourcepaths
        self.debug = debug
        self.optimize = optimize
        self.target = target
        self.flags = flags

        if not self.check_flags([]):
            raise ConfigFailed('%s failed to compile an exe' % self)

    def __call__(self, dst, src, *args,
            classpaths=[],
            sourcepaths=[],
            debug=None,
            optimize=None,
            target=None,
            flags=[],
            **kwargs):
        cmd = [self.exe]

        debug = self.debug if debug is None else debug
        if debug:
            cmd.append('-g')

        optimize = self.optimize if optimize is None else optimize
        if optimize:
            cmd.append('-optimise')

        target = self.target if target is None else target
        if target is not None:
            cmd.append('-target:' + str(target))

        cmd.extend(('-d', dst))

        classpaths = tuple(chain(self.classpaths, classpaths))
        for classpath in classpaths:
            cmd.extend(('-classpath', classpath))

        sourcepaths = tuple(chain(self.sourcepaths, sourcepaths))
        for sourcepath in sourcepaths:
            cmd.extend(('-sourcepath', sourcepath))

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

        with tempfile('', suffix='.scala') as src:
            try:
                self(src.parent, src, flags=flags, quieter=1)
            except ExecutionError as e:
                logger.failed()
                if e.stdout:
                    logger.log(e.stdout.decode())
                if e.stderr:
                    logger.log(e.stderr.decode())
                return False

        logger.passed()
        return True

    def __str__(self):
        return ' '.join([self.exe] + self.flags)

    def __eq__(self, other):
        return isinstance(other, Flx) and \
            self.exe == other.exe

# ------------------------------------------------------------------------------

class Scala(fbuild.builders.AbstractCompiler):
    def __init__(self, scala='scala', scalac='scalac', *,
            platform=None,
            classpaths=[],
            sourcepaths=[],
            debug=False,
            optimize=False,
            target=None,
            flags=[]):
        super().__init__(src_suffix='.scala')

        self.scala = fbuild.builders.find_program([scala])
        self.scalac = Scalac(scalac,
            classpaths=classpaths,
            sourcepaths=sourcepaths,
            debug=debug,
            optimize=optimize,
            target=None,
            flags=flags)

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, *args, **kwargs) -> fbuild.db.DST:
        """Compile a felix file and cache the results."""
        return self.uncached_compile(src, *args, **kwargs)

    def uncached_compile(self, src, *,
            buildroot=None,
            **kwargs):
        """Compile a felix file without caching the results.  This is needed
        when compiling temporary files."""
        src = Path(src)
        buildroot = buildroot or fbuild.buildroot
        dst = src.addroot(buildroot).parent
        dst.makedirs()

        self.scalac(dst, src, self.scalac, '%s -> %s' % (src, dst),
            color='green',
            **kwargs)

        return dst

    def build_objects(self, srcs, **kwargs):
        return fbuild.scheduler.map(partial(self.compile, **kwargs), srcs)

    def run(self, src, obj, *args, **kwargs):
        cmd = [self.scala]
        cmd.extend(('-classpath', src))
        cmd.append(obj)
        return fbuild.execute(cmd, *args, **kwargs)

    # --------------------------------------------------------------------------

    def tempfile_run(self, code='', *, quieter=1, **kwargs):
        with self.tempfile(code) as src:
            exe = self.uncached_compile(src, quieter=quieter, **ckwargs)
            return self.run(exe, quieter=quieter, **kwargs)
