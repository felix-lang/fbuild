import fbuild.packages as packages

# -----------------------------------------------------------------------------

class StaticBuilder:
    def builder(self, conf):
        return conf['c']['static']

class SharedBuilder:
    def builder(self, conf):
        return conf['c']['shared']

# -----------------------------------------------------------------------------

class _Object(packages.Package):
    def __init__(self, src, **kwargs):
        self.src = src
        self.kwargs = kwargs

    def build(self, conf):
        src = packages.build(self.src, conf)
        return self.builder(conf).compile(src, **self.kwargs)

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

    def build(self, conf):
        builder = self.builder(conf)
        return builder.link_lib( self.dst,
            [packages.build(s, conf) for s in self.srcs],
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

    def build(self, conf):
        return conf['c']['static'].link_exe(
            self.dst,
            [packages.build(s, conf) for s in self.srcs],
            libs=[packages.build(l, conf) for l in self.libs],
            destdir=self.destdir,
            **self.kwargs)
