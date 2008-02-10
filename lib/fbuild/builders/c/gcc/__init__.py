import os
from functools import partial

from fbuild import logger, ExecutionError, ConfigFailed
import fbuild.scheduler
from fbuild.path import make_path, glob_paths
import fbuild.builders.c as c

# -----------------------------------------------------------------------------

class Gcc:
    def __init__(self, exe):
        self.exe = exe

    def __str__(self):
        return self.exe

    def __call__(self, srcs, dst=None, flags=[], *, pre_flags=[], **kwargs):
        cmd = [self.exe]
        cmd.extend(pre_flags)

        if dst is not None:
            cmd.extend(('-o', dst))
            msg2 = '%s -> %s' % (' '.join(srcs), dst)
        else:
            msg2 = ' '.join(srcs)

        cmd.extend(flags)
        cmd.extend(srcs)

        from fbuild import execute
        return execute(cmd, self.exe, msg2, **kwargs)

    def check_flags(self, flags=[]):
        if flags:
            logger.check('checking %s with %s' % (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        code = 'int main(int argc, char** argv){return 0;}'

        from fbuild.temp import tempfile
        with tempfile(code, suffix='.c') as src:
            try:
                self(flags + [src], quieter=1, cwd=os.path.dirname(src))
            except ExecutionError:
                logger.log('failed', color='yellow')
                return False

        logger.log('ok', color='green')
        return True

def config_gcc(conf, exe=None, default_exes=['gcc', 'cc']):
    try:
        return conf['gcc']
    except KeyError:
        pass

    from fbuild.builders import MissingProgram, find_program
    exe = exe or find_program(default_exes)

    if not exe:
        raise MissingProgram('gcc')

    gcc = conf['gcc'] = Gcc(exe)

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

    def __str__(self):
        return ' '.join([str(self.gcc)] + self.flags)

    def __call__(self, src, dst=None, *,
            includes=[],
            warnings=[],
            macros=[],
            flags=[],
            debug=False,
            optimize=False,
            buildroot=fbuild.buildroot,
            **kwargs):
        src = make_path(fbuild.scheduler.evaluate(src))
        if dst is None:
            dst = os.path.splitext(src)[0] + self.suffix

        dst = make_path(dst, root=buildroot)
        fbuild.path.make_dirs(os.path.dirname(dst))

        cmd_flags = []

        if debug:    cmd_flags.extend(self.debug_flags)
        if optimize: cmd_flags.extend(self.optimize_flags)

        cmd_flags.extend('-I' + i for i in includes)
        cmd_flags.extend('-D' + d for d in macros)
        cmd_flags.extend('-W' + w for w in warnings)
        cmd_flags.extend(flags)

        self.gcc([src], dst, cmd_flags,
            pre_flags=self.flags,
            color='green',
            **kwargs)

        return dst

def make_compiler(conf, make_gcc=config_gcc, flags=[],
        debug_flags=['-g'],
        optimize_flags=['-O2'],
        **kwargs):
    gcc = make_gcc(conf)

    if flags and not gcc.check_flags(flags):
        raise ConfigFailed('%s does not support %s flags' % (gcc, flags))

    if not gcc.check_flags(debug_flags):
        debug_flags = []

    if not gcc.check_flags(optimize_flags):
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
            buildroot=fbuild.buildroot,
            **kwargs):
        srcs = glob_paths(fbuild.scheduler.evaluate(s) for s in srcs)
        libs = (fbuild.scheduler.evaluate(l) for l in libs)

        assert srcs or libs

        dst = make_path(dst, self.prefix, self.suffix, root=buildroot)
        fbuild.path.make_dirs(os.path.dirname(dst))

        cmd_flags = []
        cmd_flags.extend('-L' + p for p in libpaths)

        extra_srcs = []
        for lib in libs:
            if os.path.exists(lib):
                extra_srcs.append(lib)
            else:
                cmd_flags.append('-l' + lib)

        cmd_flags.extend(flags)

        self.gcc(srcs + extra_srcs, dst, cmd_flags,
            pre_flags=self.flags,
            color='cyan',
            **kwargs)

        return dst

def make_linker(conf, make_gcc=config_gcc, flags=[], **kwargs):
    gcc = make_gcc(conf)

    if flags and not gcc.check_flags(flags):
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

def make_static(conf, make_compiler, make_lib_linker, make_exe_linker,
        src_suffix='.c',  obj_suffix='.o',
        lib_prefix='lib', lib_suffix='.a',
        exe_suffix='',
        **kwargs):
    builder = Builder(
            src_suffix=src_suffix,
            compiler=make_compiler(conf, suffix=obj_suffix, **kwargs),
            lib_linker=make_lib_linker(conf,
                prefix=lib_prefix,
                suffix=lib_suffix),
            exe_linker=make_exe_linker(conf,
                prefix='',
                suffix=exe_suffix))

    c.check_builder(builder)

    return builder

def make_shared(conf, make_compiler, make_lib_linker, make_exe_linker,
        src_suffix='.c',  obj_suffix='.os',
        lib_prefix='lib', lib_suffix='.so',
        exe_suffix='',
        **kwargs):
    builder = Builder(
            src_suffix=src_suffix,
            compiler=make_compiler(conf,
                suffix=obj_suffix,
                **kwargs),
            lib_linker = make_lib_linker(conf,
                prefix=lib_prefix,
                suffix=lib_suffix),
            exe_linker=make_exe_linker(conf,
                prefix='',
                suffix=exe_suffix))

    c.check_builder(builder)

    return builder

# -----------------------------------------------------------------------------

def config_static(conf, *args,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c'],
        **kwargs):
    from ... import ar

    conf.setdefault('c', {})['static'] = make_static(conf,
        partial(make_compiler, flags=compile_flags),
        ar.config,
        make_linker,
        *args, **kwargs)

def config_shared(conf, *args,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c', '-fPIC'],
        lib_link_flags=['-shared'],
        **kwargs):
    conf.setdefault('c', {})['shared'] = make_shared(conf,
        partial(make_compiler, flags=compile_flags),
        partial(make_linker, flags=lib_link_flags),
        make_linker,
        *args, **kwargs)

def config(conf, exe=None, *args,
        config_gcc=config_gcc,
        config_static=config_static,
        config_shared=config_shared,
        **kwargs):
    config_gcc(conf, exe)
    config_static(conf, *args, **kwargs)
    config_shared(conf, *args, **kwargs)

    return conf['c']

# -----------------------------------------------------------------------------

def config_builtin_expect(conf):
    gcc = conf.setdefault('gcc', {})
    gcc['builtin_expect'] = conf['static'].check_compile('''
        int main(int argc, char** argv) {
            if(__builtin_expect(1,1));
            return 0;
        }
    ''', 'checking if supports builtin expect')

def config_named_registers_x86(conf):
    gcc = conf.setdefault('gcc', {})
    gcc['named_registers_x86'] = conf['static'].check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("esp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86 named registers')

def config_named_registers_x86_64(conf):
    gcc = conf.setdefault('gcc', {})
    gcc['named_registers_x86_64'] = conf['static'].check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("rsp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86_64 named registers')

def config_computed_gotos(conf):
    gcc = conf.setdefault('gcc', {})
    gcc['computed_gotos'] = conf['static'].check_compile('''
        int main(int argc, char** argv) {
            void *label = &&label2;
            goto *label;
        label1:
            return 1;
        label2:
            return 0;
        }
    ''', 'checking if supports computed gotos')

def config_asm_labels(conf):
    gcc = conf.setdefault('gcc', {})
    gcc['asm_labels'] = conf['static'].check_compile('''
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

def config_extensions(conf):
    config_builtin_expect(conf)
    config_named_registers_x86(conf)
    config_named_registers_x86_64(conf)
    config_computed_gotos(conf)
    config_asm_labels(conf)
