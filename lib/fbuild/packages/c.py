from itertools import chain
from functools import partial

from fbuild import scheduler
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class _Object(packages.OneToOnePackage):
    _default_builder = 'fbuild.builders.c.guess.config'

    def __init__(self, *args, builder=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.builder = builder

    def _builder(self, env):
        'Return the passed in builder or use the default one'
        if self.builder is None:
            return env.config(self._default_builder)
        return self.builder

class StaticObject(_Object):
    def command(self, env, *args, **kwargs):
        return self._builder(env).static.compile(*args, **kwargs)

class SharedObject(_Object):
    def command(self, env, *args, **kwargs):
        return self._builder(env).shared.compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(packages.ManyToOnePackage):
    _default_builder = 'fbuild.builders.c.guess.config'

    def __init__(self, dst, srcs, *,
            builder=None,
            includes=[],
            macros=[],
            libs=[],
            cflags={},
            lflags={}):
        super().__init__(dst, srcs)

        self.builder = builder
        self.includes = includes
        self.macros = macros
        self.libs = libs
        self.cflags = cflags
        self.lflags = lflags

    def dependencies(self, env):
        return chain(packages.glob_paths(self.srcs), self.libs)

    def run(self, env):
        libs = packages.build_srcs(env, self.libs)
        srcs = packages.build_srcs(env, packages.glob_paths(self.srcs))

        objs = scheduler.map(
            partial(self.compiler, env,
                includes=self.includes,
                macros=self.macros,
                **self.cflags),
            srcs)

        return self.command(env, packages.build(env, self.dst), objs,
            libs=libs,
            **self.lflags)

    def _builder(self, env):
        'Return the passed in builder or use the default one'
        if self.builder is None:
            return env.config(self._default_builder)
        return self.builder

class StaticLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return self._builder(env).static.compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return self._builder(env).static.link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return self._builder(env).shared.compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return self._builder(env).shared.link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, env, *args, **kwargs):
        return self._builder(env).static.compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return self._builder(env).static.link_exe(*args, **kwargs)
