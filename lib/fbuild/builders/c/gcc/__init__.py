from itertools import chain
import re

import fbuild
import fbuild.builders.ar
import fbuild.builders.c
import fbuild.db
import fbuild.record
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.temp import tempfile

# ------------------------------------------------------------------------------

class Gcc(fbuild.db.PersistentObject):
    def __init__(self, exe, *,
            pre_flags=[],
            flags=[],
            includes=[],
            macros=[],
            warnings=[],
            libpaths=[],
            libs=[],
            external_libs=[],
            debug=None,
            optimize=None,
            debug_flags=['-g'],
            optimize_flags=['-O2']):
        self.exe = exe
        self.pre_flags = pre_flags
        self.flags = flags
        self.includes = includes
        self.macros = macros
        self.warnings = warnings
        self.debug = debug
        self.optimize = optimize
        self.debug_flags = debug_flags
        self.optimize_flags = optimize_flags
        self.libpaths = libpaths
        self.libs = libs
        self.external_libs = external_libs

        if not self.check_flags(flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

        if debug_flags and not self.check_flags(debug_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

        if optimize_flags and not self.check_flags(optimize_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

    def __call__(self, srcs, dst=None, *,
            pre_flags=[],
            flags=[],
            includes=[],
            macros=[],
            warnings=[],
            libpaths=[],
            libs=[],
            external_libs=[],
            debug=None,
            optimize=None,
            **kwargs):
        new_includes = []
        for include in chain(self.includes, includes, (s.parent for s in srcs)):
            if include not in new_includes:
                new_includes.append(include)
        includes = new_includes

        new_flags = []
        for flag in chain(self.flags, flags):
            if flag not in new_flags:
                new_flags.append(flag)
        flags = new_flags

        macros = set(macros)
        macros.update(self.macros)

        warnings = set(warnings)
        warnings.update(self.warnings)

        new_libpaths = []
        for libpath in chain(self.libpaths, libpaths):
            if libpath not in new_libpaths:
                new_libpaths.append(libpath)
        libpaths = new_libpaths

        new_external_libs = []
        for lib in chain(self.external_libs, external_libs):
            if lib not in new_external_libs:
                new_external_libs.append(lib)
        external_libs = new_external_libs

        # Since the libs could be derived from fbuild.builders.c.Library, we need
        # to extract the extra libs and flags that they need.  Linux needs the
        # libraries listed in a particular order.  Libraries must appear left
        # of their dependencies in order to optimize linking.
        new_libs = []
        def f(lib):
            if lib in new_libs:
                return

            if isinstance(lib, fbuild.builders.c.Library):
                for flag in lib.flags:
                    if flag not in flags:
                        flags.append(flag)

                for libpath in lib.libpaths:
                    if libpath not in libpaths:
                        libpaths.append(libpath)

                for l in lib.external_libs:
                    if l not in external_libs:
                        external_libs.append(l)

                # In order to make linux happy, we'll recursively walk the
                # dependencies first, then add the library.
                for l in lib.libs:
                    f(l)

            new_libs.append(lib)

        for lib in chain(self.libs, libs):
            f(lib)

        # Finally, we need to reverse the list so it's in the proper order.
        new_libs.reverse()
        libs = new_libs

        # ----------------------------------------------------------------------

        cmd = [self.exe]
        cmd.extend(self.pre_flags)
        cmd.extend(pre_flags)

        if (debug is None and self.debug) or debug:
            cmd.extend(self.debug_flags)

        if (optimize is None and self.optimize) or optimize:
            cmd.extend(self.optimize_flags)

        # make sure that the path is converted into the native path format
        cmd.extend('-I' + Path(i) for i in sorted(includes) if i)
        cmd.extend('-D' + d for d in sorted(macros))
        cmd.extend('-W' + w for w in sorted(warnings))
        cmd.extend('-L' + Path(p) for p in sorted(libpaths) if p)

        if dst is not None:
            cmd.extend(('-o', dst))
            msg2 = '%s -> %s' % (' '.join(chain(srcs, libs)), dst)
        else:
            msg2 = ' '.join(srcs)

        cmd.extend(flags)
        cmd.extend(srcs)

        # Libraries must come last on linux in order to find symbols.
        cmd.extend('-l' + l for l in external_libs)
        cmd.extend(libs)

        return execute(cmd, str(self), msg2, **kwargs)

    def check_flags(self, flags):
        if flags:
            logger.check('checking %s with %s' % (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        code = 'int main(int argc, char** argv){return 0;}'

        with tempfile(code, suffix='.c') as src:
            try:
                self([src], flags=flags, quieter=1, cwd=src.parent)
            except ExecutionError:
                logger.failed()
                return False

        logger.passed()
        return True

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.exe,), self.flags))

    def __eq__(self, other):
        return isinstance(other, Gcc) and \
            self.exe == other.exe and \
            self.flags == other.flags and \
            self.includes == other.includes and \
            self.macros == other.macros and \
            self.warnings == other.warnings and \
            self.debug == other.debug and \
            self.optimize == other.optimize and \
            self.debug_flags == other.debug_flags and \
            self.optimize_flags == other.optimize_flags and \
            self.libpaths == other.libpaths and \
            self.libs == other.libs and \
            self.external_libs == other.external_libs

    def __hash__(self):
        return hash((
            self.exe,
            self.flags,
            self.includes,
            self.macros,
            self.warnings,
            self.debug,
            self.optimize,
            self.debug_flags,
            self.optimize_flags,
            self.libpaths,
            self.libs,
            self.external_libs,
        ))

def make_gcc(exe=None, default_exes=['gcc', 'cc'], **kwargs):
    return Gcc(
        fbuild.builders.find_program([exe] if exe else default_exes),
        **kwargs)

# ------------------------------------------------------------------------------

class Compiler(fbuild.db.PersistentObject):
    def __init__(self, gcc, flags, *, suffix):
        self.gcc = gcc
        self.flags = flags
        self.suffix = suffix

        if flags and not gcc.check_flags(flags):
            raise ConfigFailed('%s does not support %s flags' % (gcc, flags))

    def __call__(self, src, dst=None, *,
            suffix=None,
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        src = Path(src)

        suffix = suffix or self.suffix
        dst = (dst or src).addroot(buildroot).replaceext(suffix)
        dst.parent.makedirs()

        self.gcc([src], dst, pre_flags=self.flags, color='green', **kwargs)

        return dst

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.gcc,), self.flags))

    def __eq__(self, other):
        return isinstance(other, Compiler) and \
            self.gcc == other.gcc and \
            self.flags == other.flags and \
            self.suffix == other.suffix

    def __hash__(self):
        return hash((self.gcc, self.flags, self.suffix))

def make_compiler(gcc, flags=[], **kwargs):
    return Compiler(gcc, flags, **kwargs)

# ------------------------------------------------------------------------------

class Linker(fbuild.db.PersistentObject):
    def __init__(self, gcc, flags=[], *, prefix, suffix):
        self.gcc = gcc
        self.flags = flags
        self.prefix = prefix
        self.suffix = suffix

        if flags and not gcc.check_flags(flags):
            raise ConfigFailed('%s does not support %s' %
                (gcc, ' '.join(flags)))

    def __call__(self, dst, srcs, *,
            prefix=None,
            suffix=None,
            buildroot=None,
            **kwargs):
        prefix = prefix or self.prefix
        suffix = suffix or self.suffix
        buildroot = buildroot or fbuild.buildroot
        dst = Path(dst).addroot(buildroot)
        dst = dst.parent / prefix + dst.name + suffix
        dst.parent.makedirs()

        self.gcc(srcs, dst, pre_flags=self.flags, color='cyan', **kwargs)

        return dst

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.gcc,), self.flags))

    def __eq__(self, other):
        return isinstance(other, Linker) and \
                self.gcc == other.gcc and \
                self.flags == other.flags and \
                self.prefix == other.prefix and \
                self.suffix == other.suffix

    def __hash__(self):
        return hash((
            self.gcc,
            self.flags,
            self.prefix,
            self.suffix,
        ))

def make_linker(gcc, flags=[], **kwargs):
    return Linker(gcc, flags, **kwargs)

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.c.Builder):
    def __init__(self, *args,
            compiler,
            lib_linker,
            exe_linker,
            **kwargs):
        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

        # This needs to come last as the parent class tests the builder.
        super().__init__(*args, **kwargs)

    def __str__(self):
        return str(self.compiler)

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, dst=None, *,
            flags=[],
            **kwargs) -> fbuild.db.DST:
        """Compile a c file and cache the results."""
        # Generate the dependencies while we compile the file.
        with tempfile() as dep:
            obj = self.uncached_compile(src, dst,
                flags=list(chain(('-MMD', '-MF', dep), flags)),
                **kwargs)

            with open(dep, 'rb') as f:
                # Parse the output and return the module dependencies.
                stdout = f.read().replace(b'\\\n', b'')

        # Parse the output and return the module dependencies.
        m = re.match(b'\S+:(?: (.*))?$', stdout)
        if not m:
            raise ExecutionError('unable to understand %r' % stdout)

        s = m.group(1)
        if s is not None:
            deps = s.decode().split()
            fbuild.db.add_external_dependencies_to_call(srcs=deps)

        return obj

    def uncached_compile(self, *args, **kwargs):
        """Compile a c file without caching the results.  This is needed when
        compiling temporary files."""
        return self.compiler(*args, **kwargs)

    def uncached_link_lib(self, *args, **kwargs):
        """Link compiled c files into a library without caching the results.
        This is needed when linking temporary files."""
        lib = self.lib_linker(*args, **kwargs)
        return fbuild.builders.c.Library(lib,
            flags=kwargs.get('flags', []),
            libpaths=kwargs.get('libpaths', []),
            libs=kwargs.get('libs', []),
            external_libs=kwargs.get('external_libs', []))

    def uncached_link_exe(self, *args, **kwargs):
        """Link compiled c files into am executable without caching the
        results.  This is needed when linking temporary files."""
        return self.exe_linker(*args, **kwargs)

    # --------------------------------------------------------------------------

    def __repr__(self):
        return '%s(compiler=%r, lib_linker=%r, exe_linker=%r)' % (
            self.__class__.__name__,
            self.compiler,
            self.lib_linker,
            self.exe_linker)

    def __eq__(self, other):
        return isinstance(other, Builder) and \
                self.compiler == other.compiler and \
                self.lib_linker == other.lib_linker and \
                self.exe_linker == other.exe_linker

    def __hash__(self):
        return hash((
            self.compiler,
            self.lib_linker,
            self.exe_linker,
        ))

# ------------------------------------------------------------------------------

def static(exe=None, *args,
        make_gcc=make_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        platform=None,
        flags=[],
        compile_flags=['-c'],
        libpaths=[],
        libs=[],
        link_flags=[],
        exe_link_flags=[],
        src_suffix='.c',
        **kwargs):
    gcc = make_gcc(exe, libpaths=libpaths, libs=libs, **kwargs)

    return Builder(
        compiler=make_compiler(gcc,
            flags=list(chain(flags, compile_flags)),
            suffix=fbuild.builders.platform.static_obj_suffix(platform)),
        lib_linker=fbuild.builders.ar.Ar(
            libs=libs,
            libpaths=libpaths,
            prefix=fbuild.builders.platform.static_lib_prefix(platform),
            suffix=fbuild.builders.platform.static_lib_suffix(platform)),
        exe_linker=make_linker(gcc,
            flags=list(chain(flags, link_flags, exe_link_flags)),
            prefix='',
            suffix=fbuild.builders.platform.exe_suffix(platform)),
        src_suffix=src_suffix)

# ------------------------------------------------------------------------------

def shared(exe=None, *args,
        make_gcc=make_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        platform=None,
        flags=[],
        compile_flags=['-c', '-fPIC'],
        libpaths=[],
        libs=[],
        link_flags=[],
        lib_link_flags=['-fPIC', '-shared'],
        exe_link_flags=[],
        src_suffix='.c',
        **kwargs):
    gcc = make_gcc(exe, libpaths=libpaths, libs=libs, **kwargs)

    return Builder(
        compiler=make_compiler(gcc,
            flags=list(chain(flags, compile_flags)),
            suffix=fbuild.builders.platform.shared_obj_suffix(platform)),
        lib_linker=make_linker(gcc,
            flags=list(chain(flags, link_flags, lib_link_flags)),
            prefix=fbuild.builders.platform.shared_lib_prefix(platform),
            suffix=fbuild.builders.platform.shared_lib_suffix(platform)),
        exe_linker=make_linker(gcc,
            flags=list(chain(flags, link_flags, exe_link_flags)),
            prefix='',
            suffix=fbuild.builders.platform.exe_suffix(platform)),
        src_suffix=src_suffix)
