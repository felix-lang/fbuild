from itertools import chain
from functools import partial

import fbuild
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class BytecodeModule(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['bytecode'].compile

class NativeModule(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['native'].compile

class BytecodeImplementation(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['bytecode'].compile_implementation

class NativeImplementation(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['native'].compile_implementation

class BytecodeInterface(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['bytecode'].compile_interface

class NativeInterface(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['native'].compile_interface

# -----------------------------------------------------------------------------

class _Linker(packages.SimplePackage):
    def __init__(self, dst, srcs, *, includes=[], libs=[], **kwargs):
        super().__init__(dst, **kwargs)

        self.srcs = packages.glob_paths(srcs)
        self.includes = includes
        self.libs = libs

    def dependencies(self, conf):
        # filter out system libraries
        return chain(self.srcs, (lib for lib in self.libs
            if isinstance(lib, packages.AbstractPackage)))

    def run(self, conf):
        libs = packages.build_srcs(conf, self.libs)
        srcs = packages.build_srcs(conf, self.srcs)

        # make sure that we include the parent of the src and the dst in the
        # include paths
        includes = set(self.includes)
        for src in srcs:
            if src.parent:
                includes.add(src.parent)
                includes.add(src.parent.replace_root(fbuild.buildroot))

        #  Note that we don't need the -modules flag since at the point
        # all of the source files will have been evaluated
        objs = fbuild.scheduler.map_with_dependencies(
            partial(conf['ocaml']['ocamldep'], includes=includes),
            partial(self.compiler(conf),       includes=includes),
            srcs)

        objs = [obj for obj in objs if not obj.endswith('cmi')]

        return super(_Linker, self).run(conf, objs,
            includes=includes,
            libs=libs)

class BytecodeLibrary(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile

    def command(self, conf):
        return conf['ocaml']['bytecode'].link_lib

class NativeLibrary(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile

    def command(self, conf):
        return conf['ocaml']['native'].link_lib

class BytecodeExecutable(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['bytecode'].compile

    def command(self, conf):
        return conf['ocaml']['bytecode'].link_exe

class NativeExecutable(_Linker):
    def compiler(self, conf):
        return conf['ocaml']['native'].compile

    def command(self, conf):
        return conf['ocaml']['native'].link_exe

# -----------------------------------------------------------------------------

class Library(_Linker):
    '''
    Choose the native compiler if it is available, or if not available, fall
    back to the bytecode compiler.
    '''

    def compiler(self, conf):
        try:
            return conf['ocaml']['native'].compile
        except KeyError:
            return conf['ocaml']['bytecode'].compile

    def command(self, conf):
        try:
            return conf['ocaml']['native'].link_lib
        except KeyError:
            return conf['ocaml']['bytecode'].link_lib

class Executable(_Linker):
    def compiler(self, conf):
        try:
            return conf['ocaml']['native'].compile
        except KeyError:
            return conf['ocaml']['bytecode'].compile

    def command(self, conf):
        try:
            return conf['ocaml']['native'].link_exe
        except KeyError:
            return conf['ocaml']['bytecode'].link_exe

# -----------------------------------------------------------------------------

class Ocamllex(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['ocamllex']

class Ocamlyacc(packages.SimplePackage):
    def command(self, conf):
        return conf['ocaml']['ocamlyacc']
