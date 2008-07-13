from functools import partial

from fbuild import scheduler
from fbuild.path import glob_paths
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class _Compiler(packages.Package):
    def __init__(self, src, **kwargs):
        self.src = src
        self.kwargs = kwargs

    def build(self, conf):
        return self.compiler(conf)(packages.build(self.src, conf),
            **self.kwargs)

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self.src)

class StaticObject(_Compiler):
    def compiler(self, conf):
        return conf['c']['static'].compile

class SharedObject(_Compiler):
    def compiler(self, conf):
        return conf['c']['shared'].compile

# -----------------------------------------------------------------------------

class _Linker(packages.Package):
    def __init__(self, dst, srcs, *, includes=[], libs=[], **kwargs):
        self.dst = dst
        self.srcs = []
        for src in srcs:
            try:
                paths = glob_paths([src])
            except TypeError:
                self.srcs.append(src)
            else:
                self.srcs.extend(paths)
        self.includes = includes
        self.libs = libs
        self.kwargs = kwargs

    def build(self, conf):
        libs = [packages.build(l, conf) for l in self.libs]

        objs = scheduler.map(
            partial(self.compiler(conf), includes=self.includes),
            [packages.build(src, conf) for src in self.srcs])

        return self.linker(conf)(self.dst, objs,
            libs=libs,
            **self.kwargs)

    def __str__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.srcs)

class StaticLibrary(_Linker):
    def compiler(self, conf):
        return conf['c']['static'].compile

    def linker(self, conf):
        return conf['c']['static'].link_lib

class SharedLibrary(_Linker):
    def compiler(self, conf):
        return conf['c']['shared'].compile

    def linker(self, conf):
        return conf['c']['shared'].link_lib

class Executable(_Linker):
    def compiler(self, conf):
        return conf['c']['static'].compile

    def linker(self, conf):
        return conf['c']['static'].link_exe
