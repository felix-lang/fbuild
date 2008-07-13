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
        return self.compiler(conf)(
            packages.build(self.src, conf),
            **self.kwargs)

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self.src)

class BytecodeModule(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile

class NativeModule(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile

class BytecodeImplementation(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile_implementation

class NativeImplementation(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile_implementation

class BytecodeInterface(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile_interface

class NativeInterface(_Compiler):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile_interface

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
        libs = [packages.build(lib, conf) for lib in self.libs]
        srcs = [packages.build(src, conf) for src in self.srcs]

        #  Note that we don't need the -modules flag since at the point
        # all of the source files will have been evaluated
        objs = scheduler.map_with_dependencies(
            partial(conf['ocaml']['ocamldep'], includes=self.includes),
            partial(self.compiler(conf),       includes=self.includes),
            srcs)

        objs = [obj for obj in objs if not obj.endswith('cmi')]

        return self.linker(conf)(self.dst, objs,
            includes=self.includes,
            libs=libs,
            **self.kwargs)

class BytecodeLibrary(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile

    def linker(self, conf):
        return conf['ocaml']['bytecode'].link_lib

class NativeLibrary(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile

    def linker(self, conf):
        return conf['ocaml']['native'].link_lib

class BytecodeExecutable(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile

    def linker(self, conf):
        return conf['ocaml']['bytecode'].link_exe

class NativeExecutable(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile

    def linker(self, conf):
        return conf['ocaml']['native'].link_exe
