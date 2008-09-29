from itertools import chain
from functools import partial

import fbuild
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class _Object(packages.OneToOnePackage):
    default_config = 'fbuild.builders.c.guess.config'

class StaticObject(_Object):
    def command(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

class SharedObject(_Object):
    def command(self, *args, **kwargs):
        return self.config.shared.compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(packages.ManyToOnePackage):
    default_config = 'fbuild.builders.c.guess.config'

    def __init__(self, dst, srcs, *,
            includes=[],
            macros=[],
            libs=[],
            cflags={},
            lflags={},
            **kwargs):
        super().__init__(dst, srcs, **kwargs)

        self.includes = includes
        self.macros = macros
        self.libs = libs
        self.cflags = cflags
        self.lflags = lflags

    def dependencies(self):
        return chain(packages.glob_paths(self.srcs), self.libs)

    def run(self):
        libs = packages.build_srcs(self.libs)
        srcs = packages.build_srcs(packages.glob_paths(self.srcs))

        objs = fbuild.scheduler.map(
            partial(self.compiler,
                includes=self.includes,
                macros=self.macros,
                **self.cflags),
            srcs)

        return self.command(packages.build(self.dst), objs,
            libs=libs,
            **self.lflags)

class StaticLibrary(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.static.link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.shared.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.shared.link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.static.link_exe(*args, **kwargs)
