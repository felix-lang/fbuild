from itertools import chain
from functools import partial

from fbuild import scheduler
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class StaticObject(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['c']['static'].compile(*args, **kwargs)

class SharedObject(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['c']['shared'].compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(packages.ManyToOnePackage):
    def __init__(self, dst, srcs, *,
            includes=[],
            libs=[],
            cflags={},
            lflags={}):
        super().__init__(dst, packages.glob_paths(srcs))

        self.includes = includes
        self.libs = libs
        self.cflags = cflags
        self.lflags = lflags

    def dependencies(self, env):
        return chain(self.srcs, self.libs)

    def run(self, env):
        libs = packages.build_srcs(env, self.libs)
        srcs = packages.build_srcs(env, self.srcs)

        objs = scheduler.map(
            partial(self.compiler, env,
                includes=self.includes,
                **self.cflags),
            srcs)

        return self.command(env, packages.build(env, self.dst), objs,
            libs=libs,
            **self.lflags)

class StaticLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['c']['static'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['c']['static'].link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['c']['shared'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['c']['shared'].link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['c']['static'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['c']['static'].link_exe(*args, **kwargs)
