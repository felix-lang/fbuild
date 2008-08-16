from itertools import chain
from functools import partial

import fbuild.packages as packages
from fbuild.packages.c import _Linker

# -----------------------------------------------------------------------------

class StaticObject(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['cxx']['static'].compile(*args, **kwargs)

class SharedObject(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['cxx']['shared'].compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class StaticLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['cxx']['static'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['cxx']['static'].link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['cxx']['shared'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['cxx']['shared'].link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['cxx']['static'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['cxx']['static'].link_exe(*args, **kwargs)
