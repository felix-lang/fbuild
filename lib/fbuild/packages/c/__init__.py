import fbuild.packages as packages

# -----------------------------------------------------------------------------

class StaticBuilder:
    def builder(self, system):
        return system.config.c.static

class SharedBuilder:
    def builder(self, system):
        return system.config.c.shared

# -----------------------------------------------------------------------------

class _Object(packages.Package):
    def __init__(self, src, **kwargs):
        self.src = src
        self.kwargs = kwargs

    def build(self, system):
        src = packages.build(system, self.src)
        return self.builder(system).compile(src, **self.kwargs)

class StaticObject(_Object, StaticBuilder):
    pass

class SharedObject(_Object, SharedBuilder):
    pass

# -----------------------------------------------------------------------------

class _Library(packages.Package):
    def __init__(self, dst, srcs, *, destdir=None, **kwargs):
        self.dst = dst
        self.srcs = []
        for src in srcs:
            if isinstance(src, str):
                self.srcs.append(self.Object(src, destdir=destdir))
            else:
                self.srcs.append(src)
        self.destdir = destdir
        self.kwargs = kwargs

    def build(self, system):
        builder = self.builder(system)
        return builder.link_lib( self.dst,
            [packages.build(system, s) for s in self.srcs],
            destdir=self.destdir,
            **self.kwargs)

class StaticLibrary(_Library, StaticBuilder):
    Object = StaticObject

class SharedLibrary(_Library, SharedBuilder):
    Object = SharedObject

# -----------------------------------------------------------------------------

class Executable(packages.Package):
    def __init__(self, dst, srcs, libs=[], *, destdir=None, **kwargs):
        self.dst = dst
        self.srcs = []
        for src in srcs:
            if isinstance(src, str):
                self.srcs.append(StaticObject(src, destdir=destdir))
            else:
                self.srcs.append(src)
        self.libs = libs
        self.destdir = destdir
        self.kwargs = kwargs

    def build(self, system):
        return system.config.c.static.link_exe(
            self.dst,
            [packages.build(system, s) for s in self.srcs],
            libs=[packages.build(system, l) for l in self.libs],
            destdir=self.destdir,
            **self.kwargs)
