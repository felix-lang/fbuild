from itertools import chain
from functools import partial

from fbuild import scheduler
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class StaticObject(packages.SimplePackage):
    def command(self, conf):
        return conf['c']['static'].compile

class SharedObject(packages.SimplePackage):
    def command(self, conf):
        return conf['c']['shared'].compile

# -----------------------------------------------------------------------------

class _Linker(packages.SimplePackage):
    def __init__(self, dst, srcs, *, includes=[], libs=[], **kwargs):
        super().__init__(dst, **kwargs)

        self.srcs = packages.glob_paths(srcs)
        self.includes = includes
        self.libs = libs

    def dependencies(self, conf):
        return chain(self.srcs, self.libs)

    def run(self, conf):
        libs = packages.build_srcs(conf, self.libs)
        srcs = packages.build_srcs(conf, srcs)

        objs = scheduler.map(
            partial(self.compiler(conf), includes=self.includes),
            srcs)

        return super(_Linker, self).run(conf, objs, libs=libs)

class StaticLibrary(_Linker):
    def compiler(self, conf):
        return conf['c']['static'].compile

    def command(self, conf):
        return conf['c']['static'].link_lib

class SharedLibrary(_Linker):
    def compiler(self, conf):
        return conf['c']['shared'].compile

    def command(self, conf):
        return conf['c']['shared'].link_lib

class Executable(_Linker):
    def compiler(self, conf):
        return conf['c']['static'].compile

    def command(self, conf):
        return conf['c']['static'].link_exe
