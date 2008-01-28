import os
from functools import partial

from fbuild import ExecutionError, ConfigFailed
import fbuild.path
import fbuild.builders
from ... import c

# -----------------------------------------------------------------------------

class Gcc:
    def __init__(self, system, exe):
        self.system = system
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

        return self.system.execute(cmd, msg1=self.exe, msg2=msg2, **kwargs)

    def check_flags(self, flags=[]):
        if flags:
            self.system.check('checking %s with %s' % (self, ' '.join(flags)))
        else:
            self.system.check('checking %s' % self)

        with c.tempfile() as src:
            try:
                self(flags + [src], quieter=1, cwd=os.path.dirname(src))
            except ExecutionError:
                self.system.log('failed', color='yellow')
                return False

        self.system.log('ok', color='green')
        return True

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

    def __call__(self, srcs, *,
            includes=[],
            warnings=[],
            macros=[],
            flags=[],
            debug=False,
            optimize=False,
            **kwargs):
        cmd_flags = []

        if debug:
            cmd_flags.extend(self.debug_flags)

        if optimize:
            cmd_flags.extend(self.optimize_flags)

        cmd_flags.extend('-I' + i for i in includes)
        cmd_flags.extend('-D' + d for d in macros)
        cmd_flags.extend('-W' + w for w in warnings)
        cmd_flags.extend(flags)

        objects = []
        for src in fbuild.path.glob_paths(srcs):
            dst = os.path.splitext(src)[0] + self.suffix
            self.gcc([src], dst, cmd_flags,
                pre_flags=self.flags,
                color='green',
                **kwargs)

            objects.append(dst)

        return objects

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
            **kwargs):
        dst = fbuild.path.make_path(dst, self.prefix, self.suffix)
        srcs = fbuild.path.glob_paths(srcs)

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

# -----------------------------------------------------------------------------

def make_gcc(system, exe=None, default_exes=['gcc', 'cc']):
    exe = exe or fbuild.builders.find_program(system, default_exes)

    if not exe:
        raise ConfigFailed('cannot find gcc')

    gcc = Gcc(system, exe)

    if not gcc.check_flags([]):
        raise ConfigFailed('gcc failed to compile an exe')

    return gcc

def make_compiler(gcc, compile_flags,
        debug_flags=['-g'],
        optimize_flags=['-O2'],
        **kwargs):
    if compile_flags and not gcc.check_flags(compile_flags):
        raise ConfigFailed('%s does not support %s flags' %
            (gcc, compile_flags))

    if not gcc.check_flags(debug_flags):
        debug_flags = []

    if not gcc.check_flags(optimize_flags):
        optimize_flags = []

    return Compiler(gcc, compile_flags,
        debug_flags=debug_flags,
        optimize_flags=optimize_flags,
        **kwargs)

def make_linker(gcc, link_flags=[], **kwargs):
    if link_flags and not gcc.check_flags(link_flags):
        raise ConfigFailed('%s does not support %s' %
            (gcc, ' '.join(link_flags)))

    return Linker(gcc, link_flags, **kwargs)

def make_static(gcc, ar, *,
        src_suffix='.c',
        obj_suffix='.o',
        lib_prefix='lib',
        lib_suffix='.a',
        exe_suffix='',
        compile_flags=['-c'],
        exe_link_flags=[],
        **kwargs):
    return Builder(gcc.system,
            src_suffix=src_suffix,
            compiler=make_compiler(gcc, compile_flags,
                suffix=obj_suffix,
                **kwargs),
            lib_linker=ar(
                prefix=lib_prefix,
                suffix=lib_suffix),
            exe_linker=make_linker(gcc, exe_link_flags,
                prefix='',
                suffix=exe_suffix),
    )

def make_shared(gcc, *,
        src_suffix='.c',
        obj_suffix='.os',
        lib_prefix='lib',
        lib_suffix='.so',
        exe_suffix='',
        compile_flags=['-c', '-fPIC'],
        lib_link_flags=['-shared'],
        exe_link_flags=[],
        **kwargs):
    return Builder(gcc.system,
            src_suffix=src_suffix,
            compiler=make_compiler(gcc, compile_flags,
                suffix=obj_suffix,
                **kwargs),
            lib_linker = make_linker(gcc, lib_link_flags,
                prefix=lib_prefix,
                suffix=lib_suffix),
            exe_linker=make_linker(gcc, exe_link_flags,
                prefix='',
                suffix=exe_suffix),
    )

# -----------------------------------------------------------------------------

def config_builder(conf, gcc, ar, *,
        make_shared=make_shared,
        tests=[],
        optional_tests=[],
        **kwargs):
    static = conf.configure('static', make_static, gcc, ar, **kwargs)
    shared = conf.configure('shared', make_shared, gcc, **kwargs)

    for builder in static, shared:
        for test in tests:
            conf.subconfigure('', test, builder)

        for test in optional_tests:
            try:
                conf.subconfigure('', test, builder)
            except ConfigFailed:
                pass

    return static, shared

def config(conf, exe, *args, **kwargs):
    from ... import ar

    return conf.subconfigure('c', config_builder,
        make_gcc(conf.system, exe),
        partial(ar.config, conf),
        *args, **kwargs)

# -----------------------------------------------------------------------------

def detect_builtin_expect(builder):
    return builder.check_compile('''
        int main(int argc, char** argv) {
            if(__builtin_expect(1,1));
            return 0;
        }
    ''', 'checking if supports builtin expect')

def detect_named_registers_x86(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("esp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86 named registers')

def detect_named_registers_x86_64(builder):
    return builder.check_compile('''
        #include <stdio.h>
        register void *sp __asm__ ("rsp");

        int main(int argc, char** argv) {
            printf("Sp = %p\\n",sp);
            return 0;
        }
    ''', 'checking if supports x86_64 named registers')

def detect_computed_gotos(builder):
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

def detect_asm_labels(builder):
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

# -----------------------------------------------------------------------------

def config_builtin_expect(conf, builder):
    conf.configure('gcc.builtin_expect', detect_builtin_expect, builder)

def config_named_registers_x86(conf, builder):
    conf.configure('gcc.named_registers_x86',
        detect_named_registers_x86, builder)

def config_named_registers_x86_64(conf, builder):
    conf.configure('gcc.named_registers_x86_64',
        detect_named_registers_x86_64, builder)

def config_computed_gotos(conf, builder):
    conf.configure('gcc.computed_gotos', detect_computed_gotos, builder)

def config_asm_labels(conf, builder):
    conf.configure('gcc.asm_labels', detect_asm_labels, builder)

def config_extensions(conf, builder):
    config_builtin_expect(conf, builder)
    config_named_registers_x86(conf, builder)
    config_named_registers_x86_64(conf, builder)
    config_computed_gotos(conf, builder)
    config_asm_labels(conf, builder)
