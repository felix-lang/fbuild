from fbuild import ConfigFailed, ExecutionError, buildroot, env, execute, logger
from fbuild.path import Path
from fbuild.record import Record
from fbuild.temp import tempfile
from fbuild.builders import MissingProgram, find_program, c

# -----------------------------------------------------------------------------

class Gcc:
    def __init__(self, exe, flags=[]):
        # we split exe in case extra arguments were specified in the name
        self.exe, *self.flags = str.split(exe)
        self.flags.extend(flags)

    def __call__(self, srcs, dst=None, flags=[], *, pre_flags=[], **kwargs):
        cmd = [self.exe]
        cmd.extend(pre_flags)

        if dst is not None:
            cmd.extend(('-o', dst))
            msg2 = '%s -> %s' % (' '.join(srcs), dst)
        else:
            msg2 = ' '.join(srcs)

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(srcs)

        return execute(cmd, str(self), msg2, **kwargs)

    def check_flags(self, flags=[]):
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
        return ' '.join([self.exe] + self.flags)

    def __repr__(self):
        return '%s(%r%s)' % (
            self.__class__.__name__,
            self.exe,
            ', flags=%r' % self.flags if self.flags else '')

    def __eq__(self, other):
        return isinstance(other, Gcc) and self.exe == other.exe

def config_gcc(exe=None, default_exes=['gcc', 'cc']):
    exe = exe or find_program(default_exes)

    if not exe:
        raise MissingProgram('gcc')

    gcc = Gcc(exe)

    if not gcc.check_flags([]):
        raise ConfigFailed('gcc failed to compile an exe')

    return gcc

# -----------------------------------------------------------------------------

class Compiler:
    def __init__(self, gcc, flags, *, suffix,
            debug_flags=[],
            optimize_flags=[]):
        self.gcc = gcc
        self.flags = flags
        self.suffix = suffix
        self.debug_flags = debug_flags
        self.optimize_flags = optimize_flags

    def __call__(self, src, dst=None, *,
            includes=[],
            warnings=[],
            macros=[],
            flags=[],
            debug=False,
            optimize=False,
            buildroot=buildroot,
            **kwargs):
        src = Path(src)
        if dst is None:
            dst = src.replace_ext(self.suffix)

        dst = dst.replace_root(buildroot)
        dst.parent.make_dirs()

        cmd_flags = []

        if debug:    cmd_flags.extend(self.debug_flags)
        if optimize: cmd_flags.extend(self.optimize_flags)

        includes = set(includes)
        includes.add(src.parent)

        cmd_flags.extend('-I' + i for i in sorted(includes) if i)
        cmd_flags.extend('-D' + d for d in macros)
        cmd_flags.extend('-W' + w for w in warnings)
        cmd_flags.extend(flags)

        self.gcc([src], dst, cmd_flags,
            pre_flags=self.flags,
            color='green',
            **kwargs)

        return dst

    def __str__(self):
        return ' '.join([str(self.gcc)] + self.flags)

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
                self.flags == other.flags and \
                self.suffix == other.suffix and \
                self.debug_flags == other.debug_flags and \
                self.optimize_flags == other.optimize_flags

def make_compiler(gcc, flags=[],
        debug_flags=['-g'],
        optimize_flags=['-O2'],
        **kwargs):
    if flags and not env.cache(gcc.check_flags, flags):
        raise ConfigFailed('%s does not support %s flags' % (gcc, flags))

    if not env.cache(gcc.check_flags, debug_flags):
        debug_flags = []

    if not env.cache(gcc.check_flags, optimize_flags):
        optimize_flags = []

    return Compiler(gcc, flags,
        debug_flags=debug_flags,
        optimize_flags=optimize_flags,
        **kwargs)

# -----------------------------------------------------------------------------

class Linker:
    def __init__(self, gcc, flags=[], *, prefix, suffix):
        self.gcc = gcc
        self.flags = flags
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, dst, srcs, *,
            libpaths=[],
            libs=[],
            flags=[],
            buildroot=buildroot,
            **kwargs):
        srcs = Path.glob_all(srcs)

        assert srcs or libs

        dst = Path(dst).replace_root(buildroot)
        dst = dst.parent / self.prefix + dst.name + self.suffix
        dst.parent.make_dirs()

        cmd_flags = []
        cmd_flags.extend('-L' + p for p in libpaths)

        extra_srcs = []
        for lib in sorted(set(libs)):
            if lib.exists():
                extra_srcs.append(lib)
            else:
                cmd_flags.append('-l' + lib)

        cmd_flags.extend(flags)

        self.gcc(srcs + extra_srcs, dst, cmd_flags,
            pre_flags=self.flags,
            color='cyan',
            **kwargs)

        return dst

    def __str__(self):
        return ' '.join([str(self.gcc)] + self.flags)

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
                self.suffix == other.suffix

def make_linker(gcc, flags=[], **kwargs):
    if flags and not env.cache(gcc.check_flags, flags):
        raise ConfigFailed('%s does not support %s' % (gcc, ' '.join(flags)))

    return Linker(gcc, flags, **kwargs)

# -----------------------------------------------------------------------------

class Builder(c.Builder):
    def __init__(self, *args, compiler, lib_linker, exe_linker, **kwargs):
        super().__init__(*args, **kwargs)

        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

    def __str__(self):
        return str(self.compiler)

    def compile(self, *args, **kwargs):
        return self.compiler(*args, **kwargs)

    def link_lib(self, *args, **kwargs):
        return self.lib_linker(*args, **kwargs)

    def link_exe(self, *args, **kwargs):
        return self.exe_linker(*args, **kwargs)

    def __str__(self):
        return ' '.join([str(self.gcc)] + self.flags)

    def __repr__(self):
        return '%s(compiler=%r, lib_linker=%r, exe_linker=%r)' % (
            self.__class__.__name__,
            str(self.compiler),
            str(self.lib_linker),
            str(self.exe_linker))

    def __eq__(self, other):
        return isinstance(other, Builder) and \
                self.compiler == other.compiler and \
                self.lib_linker == other.lib_linker and \
                self.exe_linker == other.exe_linker

# -----------------------------------------------------------------------------

def config_static(exe=None, *args,
        config_gcc=config_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c'],
        src_suffix='.c', obj_suffix='.o',
        lib_prefix='lib', lib_suffix='.a',
        exe_suffix='',
        **kwargs):
    gcc = env.cache(config_gcc, exe)

    builder = Builder(
        compiler=env.cache(make_compiler, gcc,
            flags=compile_flags,
            suffix=obj_suffix,
            **kwargs),
        lib_linker=env.cache('fbuild.builders.ar.config',
            prefix=lib_prefix,
            suffix=lib_suffix),
        exe_linker=env.cache(make_linker, gcc,
            prefix='',
            suffix=exe_suffix),
        src_suffix=src_suffix)

    c.check_builder(builder)

    return builder

# -----------------------------------------------------------------------------

def config_shared(exe=None, *args,
        config_gcc=config_gcc,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c', '-fPIC'],
        lib_link_flags=['-shared'],
        src_suffix='.c', obj_suffix='.os',
        lib_prefix='lib', lib_suffix='.so',
        exe_suffix='',
        **kwargs):
    gcc = env.cache(config_gcc, exe)

    builder = Builder(
        compiler=env.cache(make_compiler, gcc,
            flags=compile_flags,
            suffix=obj_suffix,
            **kwargs),
        lib_linker=env.cache(make_linker, gcc,
            prefix=lib_prefix,
            suffix=lib_suffix,
            flags=lib_link_flags),
        exe_linker=env.cache(make_linker, gcc,
            prefix='',
            suffix=exe_suffix),
        src_suffix=src_suffix)

    c.check_builder(builder)

    return builder

# -----------------------------------------------------------------------------

def config_builtin_expect(builder):
    return builder.check_compile('''
        int main(int argc, char** argv) {
            if(__builtin_expect(1,1));
            return 0;
        }
    ''', 'checking if supports builtin expect')

def config_named_registers_x86(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("esp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86 named registers')

def config_named_registers_x86_64(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("rsp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86_64 named registers')

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

def config_extensions(builder):
    return Record(
        builtin_expect=env.cache(config_builtin_expect, builder),
        named_registers_x86=env.cache(config_named_registers_x86, builder),
        named_registers_x86_64=env.cache(
            config_named_registers_x86_64, builder),
        computed_gotos=env.cache(config_computed_gotos, builder),
        asm_labels=env.cache(config_asm_labels, builder),
    )
