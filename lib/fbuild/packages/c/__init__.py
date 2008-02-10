from fbuild import scheduler
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class _Compiler(packages.Package):
    def __init__(self, src, **kwargs):
        self.src = src
        self.kwargs = kwargs

    def build(self, conf):
        return scheduler.future(self.compiler(conf),
            packages.build(self.src, conf), **self.kwargs)

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
    def __init__(self, dst, srcs, libs=[], *, **kwargs):
        self.dst = dst
        self.srcs = []
        for src in srcs:
            if isinstance(src, str):
                self.srcs.append(self.compiler(src))
            else:
                self.srcs.append(src)
        self.libs = libs
        self.kwargs = kwargs

    def build(self, conf):
        srcs = (packages.build(s, conf) for s in self.srcs)
        libs = (packages.build(l, conf) for l in self.libs)
        return scheduler.future(self.linker(conf), self.dst, srcs,
            libs=libs, **self.kwargs)

    def __str__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.srcs)


class StaticLibrary(_Linker):
    compiler = StaticObject

    def linker(self, conf):
        return conf['c']['static'].link_lib

class SharedLibrary(_Linker):
    compiler = SharedObject

    def linker(self, conf):
        return conf['c']['shared'].link_lib

class Executable(_Linker):
    compiler = StaticObject

    def linker(self, conf):
        return conf['c']['static'].link_exe
