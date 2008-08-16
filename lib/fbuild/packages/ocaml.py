from itertools import chain
from functools import partial

import fbuild
import fbuild.packages as packages

# -----------------------------------------------------------------------------

class BytecodeModule(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].compile(*args, **kwargs)

class NativeModule(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['native'].compile(*args, **kwargs)

class BytecodeImplementation(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].compile_implementation(*args, **kwargs)

class NativeImplementation(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['native'].compile_implementation(*args, **kwargs)

class BytecodeInterface(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].compile_interface(*args, **kwargs)

class NativeInterface(packages.OneToOnePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['native'].compile_interface(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(packages.ManyToOnePackage):
    def __init__(self, dst, srcs, *, includes=[], libs=[], **kwargs):
        super().__init__(dst, packages.glob_paths(srcs), **kwargs)

        self.includes = includes
        self.libs = libs

    def dependencies(self, env):
        # filter out system libraries
        return chain(super().dependencies(env), (lib for lib in self.libs
            if isinstance(lib, packages.Package)))

    def src_includes(self, env):
        """
        Find all the include paths in each library. This will evaluate each
        source.
        """

        includes = set()
        for src in packages.build_srcs(env, self.srcs):
            if src.parent:
                includes.add(src.parent)
                includes.add(src.parent.replace_root(fbuild.buildroot))

        return includes

    def src_libs(self, env):
        """
        Recursively determine all of the library dependencies. This will
        evaluate each library.
        """

        # Unfortunately, library order matters to ocaml, so we can't use a
        # set.
        libs = []
        for lib in self.libs:
            # add all the sub-libraries of this library
            if isinstance(lib, _Linker):
                libs.extend(l for l in lib.src_libs(env) if l not in libs)

            # now, this library
            lib = packages.build(env, lib)
            if lib not in libs:
                libs.append(lib)

        return libs

    def run(self, env):
        libs = self.src_libs(env)
        srcs = packages.build_srcs(env, self.srcs)

        includes = set(self.includes)

        # make sure that we include the parent of the src and the dst in the
        # include paths
        includes.update(self.src_includes(env))

        # add the include paths from each library so we don't need to specify
        # the "includes" explicitly. Note that we don't use the includes from
        # each library, as this shows what is directly used.
        for lib in self.libs:
            if isinstance(lib, _Linker):
                includes.update(lib.src_includes(env))

        #  Note that we don't need the -modules flag since at the point
        # all of the source files will have been evaluated
        objs = fbuild.scheduler.map_with_dependencies(
            partial(env['ocaml']['ocamldep'], includes=includes),
            partial(self.compiler, env, includes=includes),
            srcs)

        objs = [obj for obj in objs if not obj.endswith('cmi')]

        return self.command(env, packages.build(env, self.dst), objs,
            includes=includes,
            libs=libs)

class BytecodeLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].link_lib(*args, **kwargs)

class NativeLibrary(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['ocaml']['native'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['ocaml']['native'].link_lib(*args, **kwargs)

class BytecodeExecutable(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['ocaml']['bytecode'].link_exe(*args, **kwargs)

class NativeExecutable(_Linker):
    def compiler(self, env, *args, **kwargs):
        return env['ocaml']['native'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        return env['ocaml']['native'].link_exe(*args, **kwargs)

# -----------------------------------------------------------------------------

class Library(_Linker):
    '''
    Choose the native compiler if it is available, or if not available, fall
    back to the bytecode compiler.
    '''

    def compiler(self, env, *args, **kwargs):
        try:
            return env['ocaml']['native'].compile(*args, **kwargs)
        except KeyError:
            return env['ocaml']['bytecode'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        try:
            return env['ocaml']['native'].link_lib(*args, **kwargs)
        except KeyError:
            return env['ocaml']['bytecode'].link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, env, *args, **kwargs):
        try:
            return env['ocaml']['native'].compile(*args, **kwargs)
        except KeyError:
            return env['ocaml']['bytecode'].compile(*args, **kwargs)

    def command(self, env, *args, **kwargs):
        try:
            return env['ocaml']['native'].link_exe(*args, **kwargs)
        except KeyError:
            return env['ocaml']['bytecode'].link_exe(*args, **kwargs)

# -----------------------------------------------------------------------------

class Ocamllex(packages.SimplePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['ocamllex'](*args, **kwargs)

class Ocamlyacc(packages.SimplePackage):
    def command(self, env, *args, **kwargs):
        return env['ocaml']['ocamlyacc'](*args, **kwargs)
