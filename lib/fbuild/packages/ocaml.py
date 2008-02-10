from fbuild import scheduler
from fbuild.path import glob_paths
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class _Compiler(packages.Package):
    def __init__(self, src, **kwargs):
        self.src = src
        self.kwargs = kwargs

    def build(self, conf):
        return scheduler.future(self.compiler(conf),
            packages.build(self.src, conf), **self.kwargs)

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
    def __init__(self, dst, srcs, libs=[], *, **kwargs):
        self.dst = dst
        self.srcs = []
        for src in srcs:
            if isinstance(src, str):
                for s in glob_paths([src]):
                    self.srcs.append(self.compiler(s))
            else:
                self.srcs.append(src)
        self.libs = libs
        self.kwargs = kwargs

    def build(self, conf):
        srcs = (packages.build(s, conf) for s in self.srcs)
        libs = (packages.build(l, conf) for l in self.libs)
        return scheduler.future(self.linker(conf), self.dst, srcs,
                libs=libs, **self.kwargs)

class BytecodeLibrary(_Linker):
    compiler = BytecodeModule

    def linker(self, conf):
        return conf['ocaml']['bytecode'].link_lib

class NativeLibrary(_Linker):
    compiler = NativeModule

    def linker(self, conf):
        return conf['ocaml']['native'].link_lib

class BytecodeExecutable(_Linker):
    compiler = BytecodeModule

    def linker(self, conf):
        return conf['ocaml']['bytecode'].link_exe

class NativeExecutable(_Linker):
    compiler = NativeModule

    def linker(self, conf):
        return conf['ocaml']['native'].link_exe
