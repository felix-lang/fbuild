from itertools import chain
from functools import partial

import fbuild.packages as packages
from fbuild.packages.c import _Linker

# -----------------------------------------------------------------------------

class StaticObject(packages.OneToOnePackage):
    def command(self, conf, *args, **kwargs):
        return conf['cxx']['static'].compile(*args, **kwargs)

class SharedObject(packages.OneToOnePackage):
    def command(self, conf, *args, **kwargs):
        return conf['cxx']['shared'].compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class StaticLibrary(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return conf['cxx']['static'].compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return conf['cxx']['static'].link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return conf['cxx']['shared'].compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return conf['cxx']['shared'].link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return conf['cxx']['static'].compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return conf['cxx']['static'].link_exe(*args, **kwargs)
