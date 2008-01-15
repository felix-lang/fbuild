import os
from functools import partial

import fbuild.path
import fbuild.builders
from ... import c

# -----------------------------------------------------------------------------

class Gcc(fbuild.builders.Builder):
    yaml_state = ('exe', 'prefix', 'suffix', 'color')

    def __init__(self, system, exe, *, prefix='', suffix='', color=None):
        super().__init__(system)

        self.exe = exe
        self.prefix = prefix
        self.suffix = suffix
        self.color = color

        self._gcc_cmd = None

    def __str__(self):
        return ' '.join(self.exe)

    def __repr__(self):
        return '%s(exe=%r, prefix=%r, suffix=%r, color=%r)' % (
            self.__class__.__name__,
            self.exe,
            self.prefix,
            self.suffix,
            self.color,
        )

    def _get_cmd(self):
        self._gcc_cmd = fbuild.builders.SimpleCommand(
            self.system, self.exe, self.prefix, self.suffix, '-o',
            color=self.color,
        )

        return self._gcc_cmd


class Compiler(Gcc):
    def __init__(self, system, exe, *, color='green', **kwargs):
        super().__init__(system, exe, color=color, **kwargs)

    def __call__(self, srcs,
            includes=[],
            macros=[],
            flags=[],
            **kwargs):
        cmd = self._gcc_cmd or self._get_cmd()
        cmd_flags = []
        cmd_flags.extend(['-I' + i for i in includes])
        cmd_flags.extend(['-D' + d for d in macros])
        cmd_flags.extend(flags)

        objects = []
        for src in fbuild.path.glob_paths(srcs):
            dst = os.path.splitext(src)[0]
            obj = cmd(dst, [src], cmd_flags, **kwargs)
            objects.append(obj)

        return objects


class Linker(Gcc):
    yaml_state = ('lib_prefix', 'lib_suffix')

    def __init__(self, system, exe, *,
            lib_prefix='',
            lib_suffix='',
            color='green',
            **kwargs):
        self.lib_prefix = lib_prefix
        self.lib_suffix = lib_suffix
        super().__init__(system, exe, color=color, **kwargs)

    def __call__(self, dst, srcs,
            libpaths=[],
            libs=[],
            flags=[],
            **kwargs):
        new_libpaths = []
        new_libs = []

        for lib in libs:
            dirname, basename = os.path.split(lib)
            if dirname:
                if dirname not in new_libpaths:
                    new_libpaths.append(dirname)
            elif '.' not in new_libpaths:
                new_libpaths.append('.')

            if basename.startswith(self.lib_prefix):
                basename = basename[len(self.lib_prefix):]

            if basename.endswith(self.lib_suffix):
                basename = basename[:-len(self.lib_suffix)]

            new_libs.append(basename)

        cmd = self._gcc_cmd or self._get_cmd()
        cmd_flags = []
        cmd_flags.extend(['-L' + p for p in new_libpaths])
        cmd_flags.extend(['-l' + l for l in new_libs])
        cmd_flags.extend(flags)

        return cmd(dst, srcs, post_flags=cmd_flags, **kwargs)

# -----------------------------------------------------------------------------

def make_static(system, *,
        exe=None,
        src_suffix='.c',
        obj_suffix='.o',
        lib_prefix='lib',
        lib_suffix='.a',
        exe_suffix='',
        compile_flags=['-c'],
        lib_link_flags=[],
        exe_link_flags=[]):
    exe = exe or fbuild.builders.find_program(system, 'gcc', 'cc')

    from ... import ar

    return c.make_builder(system,
        partial(Compiler, exe=[exe] + compile_flags),
        ar.make,
        partial(Linker, exe=[exe] + exe_link_flags),
        src_suffix, obj_suffix, lib_prefix, lib_suffix, exe_suffix,
    )

def make_shared(system, *,
        exe=None,
        src_suffix='.c',
        obj_suffix='.os',
        lib_prefix='lib',
        lib_suffix='.so',
        exe_suffix='',
        compile_flags=['-c', '-fPIC'],
        lib_link_flags=['-shared'],
        exe_link_flags=[]):
    exe = exe or fbuild.builders.find_program(system, 'gcc', 'cc')

    return c.make_builder(system,
        partial(Compiler, exe=[exe] + compile_flags),
        partial(Linker, exe=[exe] + lib_link_flags),
        partial(Linker, exe=[exe] + exe_link_flags),
        src_suffix, obj_suffix, lib_prefix, lib_suffix, exe_suffix,
    )

# -----------------------------------------------------------------------------

def config_builder(conf, make_builder, *, **kwargs):
    builder = c.config_builder(conf, make_builder, **kwargs)

    conf.configure('debug',    c.config_compile_flags, builder, ['-g'])
    conf.configure('optimize', c.config_compile_flags, builder, ['-O2'])

    return builder

# -----------------------------------------------------------------------------

def config_static(conf, *, **kwargs):
    conf.subconfigure('static', config_builder, make_static, **kwargs)

def config_shared(conf, *, **kwargs):
    conf.subconfigure('shared', config_builder, make_shared, **kwargs)

def config(conf, *, **kwargs):
    config_static(conf, **kwargs)
    config_shared(conf, **kwargs)
