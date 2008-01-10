import os

from .. import builders
from ... import c

# -----------------------------------------------------------------------------

#@fbuild.system.system_cache
def find_gcc_exe(system, exe_names=None):
    if exe_names is None:
        exe_names = ['gcc', 'cc']
    return builders.find_program(system, exe_names)

# -----------------------------------------------------------------------------

class Gcc(builders.Builder):
    yaml_tag = '!Gcc'

    def __init__(self, system, gcc,
            prefix='',
            suffix='',
            color=None):
        super().__init__(system)

        self.gcc = gcc
        self.prefix = prefix
        self.suffix = suffix
        self.color = color

    def __repr__(self):
        return '%s(%r, prefix=%r, suffix=%r, color=%r)' % (
            self.__class__.__name__,
            self.gcc,
            self.prefix,
            self.suffix,
            self.color,
        )

    def _make_cmd(self):
        return builders.SimpleCommand(
            self.system, self.gcc, self.prefix, self.suffix, '-o',
            color=self.color,
        )


class GccCompiler(Gcc):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', 'green')
        super().__init__(*args, **kwargs)

    def __call__(self, srcs,
            includes=[],
            macros=[],
            flags=[],
            **kwargs):
        cmd = self._make_cmd()
        cmd_flags = []
        cmd_flags.extend(['-I' + i for i in includes])
        cmd_flags.extend(['-D' + d for d in macros])
        cmd_flags.extend(flags)

        objects = []
        for src in srcs:
            dst = os.path.splitext(src)[0]
            obj = cmd(dst, [src], cmd_flags, **kwargs)
            objects.append(obj)

        return objects


class GccLinker(Gcc):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('color', 'cyan')
        self.lib_prefix = kwargs.pop('lib_prefix', '')
        self.lib_suffix = kwargs.pop('lib_suffix', '')
        super().__init__(*args, **kwargs)

    def __call__(self, dst, srcs,
            libpaths=[],
            libs=[],
            flags=[],
            **kwargs):
        new_libpaths = []
        new_libs = []

        for lib in libs:
            dirname, basename = os.path.split(lib)
            if dirname and dirname not in libpaths:
                new_libpaths.append(dirname)

            if basename.startswith(self.lib_prefix):
                basename = basename[len(self.lib_prefix):]

            if basename.endswith(self.lib_suffix):
                basename = basename[:-len(self.lib_suffix)]

            new_libs.append(basename)

        cmd = self._make_cmd()
        cmd_flags = []
        cmd_flags.extend(['-L' + p for p in new_libpaths])
        cmd_flags.extend(['-l' + l for l in new_libs])
        cmd_flags.extend(flags)

        return cmd(dst, srcs, post_flags=cmd_flags, **kwargs)

# -----------------------------------------------------------------------------

#@fbuild.system.system_cache
def config_compile_static(system, *args, **kwargs):
    gcc = [find_gcc_exe(system), '-c']
    compiler = GccCompiler(system, gcc, *args, **kwargs)

    c.check_compiler(compiler)

    return compiler


#@fbuild.system.system_cache
def config_compile_shared(system, *args, **kwargs):
    gcc = [find_gcc_exe(system), '-c', '-fPIC']
    compiler = GccCompiler(system, gcc, *args, **kwargs)

    c.check_compiler(compiler)

    return compiler


#@fbuild.system.system_cache
def config_link_staticlib(system, *args, **kwargs):
    gcc = [find_gcc_exe(system), '-static']
    return GccLinker(system, gcc, *args, **kwargs)


#@fbuild.system.system_cache
def config_link_sharedlib(system, *args, **kwargs):
    gcc = [find_gcc_exe(system), '-shared']
    return GccLinker(system, gcc, *args, **kwargs)


#@fbuild.system.system_cache
def config_link_exe(system, *args, **kwargs):
    gcc = [find_gcc_exe(system)]
    return GccLinker(system, gcc, *args, **kwargs)

# -----------------------------------------------------------------------------

class GccBuilder(c.Builder):
    def __init__(self, system, compiler, lib_linker, exe_linker):
        super().__init__(system)

        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

    def compile(self, *args, **kwargs):
        return self.compiler(*args, **kwargs)

    def link_lib(self, *args, **kwargs):
        return self.lib_linker(*args, **kwargs)

    def link_exe(self, *args, **kwargs):
        return self.exe_linker(*args, **kwargs)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__,
            self.compiler,
            self.lib_linker,
            self.exe_linker,
        )

# -----------------------------------------------------------------------------

def config_builder(system,
        config_compiler, config_lib_linker, config_exe_linker,
        obj_suffix, lib_prefix, lib_suffix, exe_suffix):
    builder = GccBuilder(system,
        config_compiler(system, suffix=obj_suffix),
        config_lib_linker(system),
        #    prefix=lib_prefix, suffix=lib_suffix,
        #    lib_prefix=lib_prefix, lib_suffix=lib_suffix),
        config_exe_linker(system, suffix=exe_suffix,
            lib_prefix=lib_prefix, lib_suffix=lib_suffix),
    )

    c.check_builder(builder)

    return builder


#@fbuild.system.system_cache
def config_static(system,
        obj_suffix='.o',
        lib_prefix='lib',
        lib_suffix='.a',
        exe_suffix=''):
    from ... import ar

    return config_builder(system,
        config_compile_static,
        ar.config_link_staticlib(system, prefix=lib_prefix, suffix=lib_suffix),
        #ar.Ar(prefix=lib_prefix, suffix=lib_suffix),
        #ar.Ar(prefix=lib_prefix, suffix=lib_suffix),
        config_link_exe,
        '.o', 'lib', '.a', '')


#@fbuild.system.system_cache
def config_shared(system,
        obj_suffix='.os',
        lib_prefix='lib',
        lib_suffix='.so',
        exe_suffix=''):
    return config_builder(system,
        config_compile_shared, config_link_sharedlib, config_link_exe,
        '.os', 'lib', '.so', '')
