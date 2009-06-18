import io
import re
import sys
from functools import partial
from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.java
import fbuild.db
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.temp import tempfile

# ------------------------------------------------------------------------------

class _Compiler:
    def __init__(self, exe, *,
            classpaths=[],
            sourcepaths=[],
            debug=False,
            optimize=False,
            debug_flags=['-g'],
            optimize_flags=['-optimise'],
            target=None,
            flags=[]):
        self.exe = fbuild.builders.find_program([exe])
        self.classpaths = classpaths
        self.sourcepaths = sourcepaths
        self.debug = debug
        self.optimize = optimize
        self.optimize_flags = optimize_flags
        self.target = target
        self.flags = flags

        if not self.check_flags([]):
            raise ConfigFailed('%s failed to compile an exe' % self)

        if debug_flags and not self.check_flags(debug_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

        if optimize_flags and not self.check_flags(optimize_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

    def _run(self, srcs, *args,
            dst=None,
            classpaths=[],
            sourcepaths=[],
            debug=None,
            optimize=None,
            target=None,
            flags=[],
            **kwargs):
        """Run scalac on the arguments."""

        assert len(srcs) > 0, "%s: no sources passed in" % dst

        cmd = [self.exe]

        if dst is not None:
            cmd.extend(('-d', dst))

        if (debug is None and self.debug) or debug:
            cmd.extend(self.debug_flags)

        if (optimize is None and self.optimize) or optimize:
            cmd.extend(self.optimize_flags)

        target = self.target if target is None else target
        if target is not None:
            cmd.append('-target:' + str(target))

        classpaths = tuple(chain(self.classpaths, classpaths))
        for classpath in classpaths:
            cmd.extend(('-cp', classpath))

        sourcepaths = tuple(chain(self.sourcepaths, sourcepaths))
        for sourcepath in sourcepaths:
            cmd.extend(('-sourcepath', sourcepath))

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(srcs)

        return execute(cmd, *args, **kwargs)

    def check_flags(self, flags=[]):
        """Verify that scalac can run with these flags."""

        if flags:
            logger.check('checking %s with %s' %
                (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        with tempfile('', suffix='.scala') as src:
            try:
                self._run([src], flags=flags, quieter=1)
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
        return isinstance(other, type(self)) and \
            self.exe == other.exe and \
            self.classpaths == other.classpaths and \
            self.sourcepaths == other.sourcepaths and \
            self.debug == other.debug and \
            self.optimize == other.optimize and \
            self.optimize_flags == other.optimize_flags and \
            self.target == other.target and \
            self.flags == other.flags

# ------------------------------------------------------------------------------

class Scala(_Compiler):
    def __init__(self, exe='scala', *args, **kwargs):
        super().__init__(exe, *args, **kwargs)

    def __call__(self, srcs, *args, flags=[], buildroot=None, **kwargs):
        """Run a scala script."""

        assert len(srcs) > 0, "%s: no sources passed in" % dst

        src = Path(srcs[0])
        buildroot = buildroot or fbuild.buildroot
        src_buildroot = src.addroot(buildroot)
        dst = src.replaceext('.jar')

        # We need to copy the src into the buildroot so we don't pollute our
        # tree.
        if src != src_buildroot:
            src_buildroot.parent.makedirs()
            src.copy(src_buildroot)
            src = src_buildroot

        # Always save the compilation results.
        flags = list(flags)
        flags.append('-savecompiled')

        stdout, stderr = super()._run(srcs, *args, flags=flags, **kwargs)
        return dst, stdout, stderr

# ------------------------------------------------------------------------------

class Scalac(_Compiler):
    def __init__(self, exe='scalac', *args, **kwargs):
        super().__init__(exe, *args, **kwargs)

    def __call__(self, dst, srcs, *args, buildroot=None, **kwargs):
        """Run a scala script."""

        dst = Path(dst).addroot(buildroot or fbuild.buildroot)
        dst.makedirs()

        stdout, stderr = self._run(srcs, *args, dst=dst, **kwargs)
        return dst, stdout, stderr

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.AbstractLibLinker, fbuild.builders.AbstractRunner):
    def __init__(self, *,
            scala='scala',
            scalac='scalac',
            jar='jar',
            java='java',
            **kwargs):
        super().__init__(src_suffix='.scala')

        self.scala = Scala(scala)
        self.scalac = Scalac(scalac, **kwargs)
        self.jar = fbuild.builders.java.Jar(jar)
        self.java = fbuild.builders.java.Java(java)

    # --------------------------------------------------------------------------

    def where(self):
        """Return the scala library directory."""
        return self.scalac.exe.realpath().parent.parent / 'lib'

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, *args,
            **kwargs) -> fbuild.db.DSTS:
        """Compile a felix file and cache the results."""
        return self.uncached_compile(src, *args, **kwargs)

    _dep_regex = re.compile(r'\[wrote (.*)\]\n')

    def uncached_compile(self, src, dst=None, *,
            flags=[],
            quieter=0,
            stderr_quieter=0,
            buildroot=None,
            **kwargs):
        """Compile a felix file without caching the results.  This is needed
        when compiling temporary files."""
        src = Path(src)
        dst = Path(dst or src.parent).addroot(buildroot or fbuild.buildroot)

        # Extract the generated files when we compile the file.
        try:
            dst, stdout, stderr = self.scalac(dst, [src],
                flags=list(chain(('-verbose',), flags)),
                quieter=quieter,
                stderr_quieter=1 if stderr_quieter == 0 else stderr_quieter,
                **kwargs)
        except fbuild.ExecutionError as e:
            if quieter == 0 and stderr_quieter == 0:
                # We errored out, but we've hidden the stderr output.
                for line in io.StringIO(e.stderr.decode()):
                    if not line.startswith('['):
                        fbuild.logger.write(line)
            raise e

        # Parse the output and find what files we generated.
        dsts = []
        for line in io.StringIO(stderr.decode()):
            m = self._dep_regex.match(line)
            if m:
                dsts.append(Path(m.group(1)))
            elif quieter == 0 and stderr_quieter == 0:
                if not line.startswith('['):
                    fbuild.logger.write(line)

        # Log all the files we found
        fbuild.logger.check(str(self.scalac),
            '%s -> %s' % (src, ' '.join(dsts)),
            color='green')

        return dsts

    # --------------------------------------------------------------------------

    def link_lib(self, *args, **kwargs):
        """Link all the L{srcs} into a library and cache the result."""
        return self.jar.create(*args, **kwargs)

    def uncached_link_lib(self, *args, **kwargs):
        """Link all the L{srcs} into a library."""
        return self.jar.uncached_create(*args, **kwargs)

    # --------------------------------------------------------------------------

    def build_objects(self, srcs:fbuild.db.SRCS, **kwargs) -> fbuild.db.DSTS:
        """Compile all the L{srcs} in parallel."""
        dsts = []
        for d in fbuild.scheduler.map(partial(self.compile, **kwargs), srcs):
            dsts.extend(d)

        return dsts

    def build_lib(self, dst, srcs, *args,
            cwd=None,
            ckwargs={},
            lkwargs={},
            **kwargs):
        """Compile all the L{srcs} and link into a library."""
        objs = self.build_objects(srcs, *args, **dict(ckwargs, **kwargs))
        return self.link_lib(dst, objs, cwd=cwd, **lkwargs)

    # --------------------------------------------------------------------------

    def run_script(self, src, *args, **kwargs):
        """Run a scala script."""
        return self.scala((src,), *args, **kwargs)

    def run_jar(self, *args, classpaths=[], **kwargs):
        """Run a scala library."""
        # Automatically add the scala-library.jar to the classpath
        classpaths = list(classpaths)
        classpaths.append(self.where() / 'scala-library.jar')

        return self.java.run_class(*args, classpaths=classpaths, **kwargs)

    # --------------------------------------------------------------------------

    def tempfile_run(self, code='', *, quieter=1, ckwargs={}, **kwargs):
        """Execute a temporary scala file."""
        with self.tempfile(code) as src:
            exe = self.uncached_compile(src, quieter=quieter, **ckwargs)
            return self.run(exe, quieter=quieter, **kwargs)
