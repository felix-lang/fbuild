from itertools import chain

import fbuild
import fbuild.builders.ar
import fbuild.db
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.record import Record
from fbuild.temp import tempfile
from fbuild.builders import MissingProgram, find_program, c

# ------------------------------------------------------------------------------

class Gcc:
    def __init__(self, exe, flags=()):
        # we split exe in case extra arguments were specified in the name
        self.exe, *self.flags = str.split(exe)
        self.flags = tuple(chain(self.flags, flags))

    def __call__(self, srcs, dst=None, flags=(), *,
            pre_flags=(),
            includes=(),
            macros=(),
            warnings=(),
            libpaths=(),
            libs=(),
            **kwargs):
        cmd = [self.exe]
        cmd.extend(pre_flags)

        # make sure that the path is converted into the native path format
        cmd.extend('-I' + Path(i) for i in sorted(includes) if i)
        cmd.extend('-D' + d for d in sorted(macros))
        cmd.extend('-W' + w for w in sorted(warnings))
        cmd.extend('-L' + p for p in sorted(libpaths) if p)
        cmd.extend('-l' + l for l in sorted(libs))

        if dst is not None:
            cmd.extend(('-o', dst))
            msg2 = '%s -> %s' % (' '.join(srcs), dst)
        else:
            msg2 = ' '.join(srcs)

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(srcs)

        return execute(cmd, str(self), msg2, **kwargs)

    def check_flags(self, flags=()):
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

    def __repr__(self):
        return '%s(%r%s)' % (
            self.__class__.__name__,
            self.exe,
            ', flags=%r' % self.flags if self.flags else '')

    def __eq__(self, other):
        return isinstance(other, Gcc) and self.exe == other.exe

    def __hash__(self):
        return hash((self.exe, self.flags))

def make_gcc(exe=None, default_exes=['gcc', 'cc']):
    exe = exe or find_program(default_exes)

    if not exe:
        raise MissingProgram('gcc')

    gcc = Gcc(exe)

    if not gcc.check_flags(()):
        raise ConfigFailed('gcc failed to compile an exe')

    return gcc

# ------------------------------------------------------------------------------

class Scanner:
    def __init__(self, gcc, flags):
        self.gcc = gcc
        self.flags = flags

    def __call__(self, src, *,
            includes=[],
            buildroot=None,
            quieter=0,
            **kwargs):
        # Ignore the buildroot argument
        src = Path(src)

        fbuild.logger.check(' * %s %s' % (self.gcc, ' '.join(self.flags)), src,
            verbose=quieter,
            color='yellow')

        includes = set(includes)
        includes.add(src.parent)

        stdout, stderr = self.gcc((src,),
            flags=list(chain(self.flags, kwargs.pop('flags', ()))),
            includes=includes,
            quieter=quieter,
            stdout_quieter=1 if quieter == 0 else quieter,
            **kwargs)

        stdout = stdout.decode().replace('\\\n', '')

        if not stdout:
            return []

        # Parse the output and return the module dependencies.
        return [Path(p)
            for p in stdout.split(':')[1].split()]

# ------------------------------------------------------------------------------

class Compiler:
    def __init__(self, gcc, flags, *, suffix,
            includes=(),
            macros=(),
            warnings=(),
            debug=None,
            optimize=None,
            debug_flags=(),
            optimize_flags=()):
        self.gcc = gcc
        self.suffix = suffix
        self.includes = tuple(includes)
        self.macros = tuple(macros)
        self.warnings = tuple(warnings)
        self.flags = tuple(flags)
        self.debug = debug
        self.optimize = optimize
        self.debug_flags = tuple(debug_flags)
        self.optimize_flags = tuple(optimize_flags)

    def __call__(self, src, dst=None, *,
            suffix=None,
            includes=(),
            macros=(),
            warnings=(),
            flags=(),
            debug=None,
            optimize=None,
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        src = Path(src)

        suffix = suffix or self.suffix
        dst = (dst or src).addroot(buildroot).replaceext(suffix)
        dst.parent.makedirs()

        cmd_flags = []

        if debug is None and self.debug or debug:
            cmd_flags.extend(self.debug_flags)

        if optimize is None and self.optimize or optimize:
            cmd_flags.extend(self.optimize_flags)

        includes = set(includes)
        includes.update(self.includes)
        includes.add(src.parent)

        macros = set(macros)
        macros.update(self.macros)

        warnings = set(warnings)
        warnings.update(self.warnings)

        cmd_flags.extend(self.flags)
        cmd_flags.extend(flags)

        self.gcc([src], dst, cmd_flags,
            pre_flags=self.flags,
            includes=includes,
            macros=macros,
            warnings=warnings,
            color='green',
            **kwargs)

        return dst

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.gcc,), self.flags))

    def __repr__(self):
        return '%s(%r, %r, debug_flags=%r, optimize_flags=%r, suffix=%r)' % (
            self.__class__.__name__,
            self.gcc,
            self.flags,
            self.debug_flags,
            self.optimize_flags,
            self.suffix)

    def __eq__(self, other):
        return isinstance(other, Compiler) and \
                self.gcc == other.gcc and \
                self.suffix == other.suffix and \
                self.macros == other.macros and \
                self.warnings == other.warnings and \
                self.flags == other.flags and \
                self.debug == other.debug and \
                self.optimize == other.optimize and \
                self.debug_flags == other.debug_flags and \
                self.optimize_flags == other.optimize_flags

    def __hash__(self):
        return hash((
            self.gcc,
            self.flags,
            self.suffix,
            self.macros,
            self.warnings,
            self.flags,
            self.debug,
            self.optimize,
            self.debug_flags,
            self.optimize_flags,
        ))

def make_compiler(gcc, flags=(), *,
        debug_flags=['-g'],
        optimize_flags=['-O2'],
        **kwargs):
    if flags and not gcc.check_flags(flags):
        raise ConfigFailed('%s does not support %s flags' % (gcc, flags))

    if not gcc.check_flags(debug_flags):
        debug_flags = ()

    if not gcc.check_flags(optimize_flags):
        optimize_flags = ()

    return Compiler(gcc, flags,
        debug_flags=debug_flags,
        optimize_flags=optimize_flags,
        **kwargs)

# ------------------------------------------------------------------------------

class Linker:
    def __init__(self, gcc, flags=(), *, prefix, suffix,
            libpaths=(),
            libs=()):
        self.gcc = gcc
        self.flags = tuple(flags)
        self.prefix = prefix
        self.suffix = suffix
        self.libpaths = tuple(libpaths)
        self.libs = tuple(libs)
        self.flags = tuple(flags)

    def __call__(self, dst, srcs, *,
            prefix=None,
            suffix=None,
            libpaths=(),
            libs=(),
            flags=(),
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot

        assert srcs or libs, 'no sources passed into gcc'

        prefix = prefix or self.prefix
        suffix = suffix or self.suffix
        dst = Path(dst).addroot(buildroot)
        dst = dst.parent / prefix + dst.name + suffix
        dst.parent.makedirs()

        libpaths = set(libpaths)
        libpaths.update(self.libpaths)

        cmd_flags = []

        libs = set(libs)
        libs.update(self.libs)

        extra_srcs = []
        new_libs = []
        for lib in sorted(libs):
            if Path(lib).exists():
                extra_srcs.append(lib)
            else:
                new_libs.append(lib)

        cmd_flags.extend(flags)

        self.gcc(srcs + extra_srcs, dst, cmd_flags,
            pre_flags=self.flags,
            libpaths=libpaths,
            libs=new_libs,
            color='cyan',
            **kwargs)

        return dst

    def __repr__(self):
        return '%s(%r, %r, prefix=%r, suffix=%r)' % (
            self.__class__.__name__,
            self.gcc,
            self.flags,
            self.prefix,
            self.suffix)

    def __eq__(self, other):
        return isinstance(other, Linker) and \
                self.gcc == other.gcc and \
                self.flags == other.flags and \
                self.prefix == other.prefix and \
                self.suffix == other.suffix and \
                self.libpaths == other.libpaths and \
                self.libs == other.libs and \
                self.flags == other.flags

    def __hash__(self):
        return hash((
            self.gcc,
            self.flags,
            self.prefix,
            self.suffix,
            self.libpaths,
            self.libs,
            self.flags,
        ))

def make_linker(gcc, flags=(), **kwargs):
    if flags and not gcc.check_flags(flags):
        raise ConfigFailed('%s does not support %s' % (gcc, ' '.join(flags)))

    return Linker(gcc, flags, **kwargs)

# ------------------------------------------------------------------------------

class Builder(c.Builder):
    def __init__(self, *args,
            scanner,
            compiler,
            lib_linker,
            exe_linker,
            **kwargs):
        super().__init__(*args, **kwargs)

        self.scanner = scanner
        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

    def __str__(self):
        return str(self.compiler)

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def scan(self, src:fbuild.db.SRC, *args, **kwargs):
        """Scan a c file for dependencies and cache the results."""
        return self.scanner(src, *args, **kwargs)

    def uncached_compile(self, *args, **kwargs):
        """Compile a c file without caching the results.  This is needed when
        compiling temporary files."""
        return self.compiler(*args, **kwargs)

    def uncached_link_lib(self, *args, **kwargs):
        """Link compiled c files into a library without caching the results.
        This is needed when linking temporary files."""
        return self.lib_linker(*args, **kwargs)

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

@fbuild.db.caches
def config_static(exe=None, *args,
        make_gcc=make_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        scan_flags=['-MM'],
        compile_flags=['-c'],
        libpaths=(),
        libs=(),
        src_suffix='.c', obj_suffix='.o',
        lib_prefix='lib', lib_suffix='.a',
        exe_suffix='',
        **kwargs):
    gcc = make_gcc(exe)

    builder = Builder(
        scanner=Scanner(gcc, flags=scan_flags),
        compiler=make_compiler(gcc,
            flags=compile_flags,
            suffix=obj_suffix,
            **kwargs),
        lib_linker=fbuild.builders.ar.config(
            libs=libs,
            libpaths=libpaths,
            prefix=lib_prefix,
            suffix=lib_suffix),
        exe_linker=make_linker(gcc,
            libs=libs,
            libpaths=libpaths,
            prefix='',
            suffix=exe_suffix),
        src_suffix=src_suffix)

    c.check_builder(builder)

    return builder

# ------------------------------------------------------------------------------

@fbuild.db.caches
def config_shared(exe=None, *args,
        make_gcc=make_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        scan_flags=['-MM'],
        compile_flags=['-c', '-fPIC'],
        libpaths=(),
        libs=(),
        lib_link_flags=['-fPIC', '-shared'],
        src_suffix='.c', obj_suffix='.os',
        lib_prefix='lib', lib_suffix='.so',
        exe_suffix='',
        **kwargs):
    gcc = make_gcc(exe)

    builder = Builder(
        scanner=Scanner(gcc, flags=scan_flags),
        compiler=make_compiler(gcc,
            flags=compile_flags,
            suffix=obj_suffix,
            **kwargs),
        lib_linker=make_linker(gcc,
            libs=libs,
            libpaths=libpaths,
            prefix=lib_prefix,
            suffix=lib_suffix,
            flags=lib_link_flags),
        exe_linker=make_linker(gcc,
            libs=libs,
            libpaths=libpaths,
            prefix='',
            suffix=exe_suffix),
        src_suffix=src_suffix)

    c.check_builder(builder)

    return builder

# ------------------------------------------------------------------------------

@fbuild.db.caches
def config_builtin_expect(builder):
    return builder.check_compile('''
        int main(int argc, char** argv) {
            if(__builtin_expect(1,1));
            return 0;
        }
    ''', 'checking if supports builtin expect')

@fbuild.db.caches
def config_named_registers_x86(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("esp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86 named registers')

@fbuild.db.caches
def config_named_registers_x86_64(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("rsp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86_64 named registers')

@fbuild.db.caches
def config_computed_gotos(builder):
    return builder.check_compile('''
        int main(int argc, char** argv) {
            void *label = &&label2;
            goto *label;
        label1:
            return 1;
        label2:
            return 0;
        }
    ''', 'checking if supports computed gotos')

@fbuild.db.caches
def config_asm_labels(builder):
    return builder.check_compile('''
        int main(int argc, char** argv) {
            void *label = &&label2;
            __asm__(".global fred");
            __asm__("fred:");
            __asm__(""::"g"(&&label1));
            goto *label;
        label1:
            return 1;
        label2:
            return 0;
        }
    ''', 'checking if supports asm labels')

@fbuild.db.caches
def config_extensions(builder):
    return Record(
        builtin_expect=config_builtin_expect(builder),
        named_registers_x86=config_named_registers_x86(builder),
        named_registers_x86_64=config_named_registers_x86_64(builder),
        computed_gotos=config_computed_gotos(builder),
        asm_labels=config_asm_labels(builder),
    )
