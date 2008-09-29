from itertools import chain
from functools import partial

import fbuild
import fbuild.packages as packages
from fbuild import env

# -----------------------------------------------------------------------------

class BytecodeModule(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_bytecode'

    def command(self, *args, **kwargs):
        return self.config.compile(*args, **kwargs)

class NativeModule(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_native'

    def command(self, *args, **kwargs):
        return self.config.compile(*args, **kwargs)

class BytecodeImplementation(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_bytecode'

    def command(self, *args, **kwargs):
        return self.config.compile_implementation(*args, **kwargs)

class NativeImplementation(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_native'

    def command(self, *args, **kwargs):
        return self.config.compile_implementation(*args, **kwargs)

class BytecodeInterface(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_bytecode'

    def command(self, *args, **kwargs):
        return self.config.compile_interface(*args, **kwargs)

class NativeInterface(packages.OneToOnePackage):
    default_config = 'fbuild.builders.ocaml.config_native'

    def command(self, *args, **kwargs):
        return self.config.compile_interface(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(packages.ManyToOnePackage):
    def __init__(self, dst, srcs, *, includes=[], libs=[], **kwargs):
        super().__init__(dst, srcs, **kwargs)

        self.includes = includes
        self.libs = libs

    def dependencies(self):
        # filter out system libraries
        return chain(
            packages.glob_paths(self.srcs),
            (lib for lib in self.libs if isinstance(lib, packages.Package)))

    def src_includes(self):
        """
        Find all the include paths in each library. This will evaluate each
        source.
        """

        includes = set()
        for src in packages.build_srcs(packages.glob_paths(self.srcs)):
            if src.parent:
                includes.add(src.parent)
                includes.add(src.parent.replace_root(fbuild.buildroot))

        return includes

    def src_libs(self):
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
                libs.extend(l for l in lib.src_libs() if l not in libs)

            # now, this library
            lib = packages.build(lib)
            if lib not in libs:
                libs.append(lib)

        return libs

    def run(self):
        libs = self.src_libs()
        srcs = packages.build_srcs(packages.glob_paths(self.srcs))

        includes = set(self.includes)

        # make sure that we include the parent of the src and the dst in the
        # include paths
        includes.update(self.src_includes())

        # add the include paths from each library so we don't need to specify
        # the "includes" explicitly. Note that we don't use the includes from
        # each library, as this shows what is directly used.
        for lib in self.libs:
            if isinstance(lib, _Linker):
                includes.update(lib.src_includes())

        ocaml = env.cache('fbuild.builders.ocaml.config')

        #  Note that we don't need the -modules flag since at the point
        # all of the source files will have been evaluated
        objs = fbuild.scheduler.map_with_dependencies(
            partial(ocaml.ocamldep, includes=includes),
            partial(self.compiler, includes=includes),
            srcs)

        objs = [obj for obj in objs if not obj.endswith('cmi')]

        return self.command(packages.build(self.dst), objs,
            includes=includes,
            libs=libs)

    def compiler(self, *args, **kwargs):
        return self.config.compile(*args, **kwargs)

class BytecodeLibrary(_Linker):
    default_config = 'fbuild.builders.ocaml.config_bytecode'

    def command(self, *args, **kwargs):
        return self.config.link_lib(*args, **kwargs)

class NativeLibrary(_Linker):
    default_config = 'fbuild.builders.ocaml.config_native'

    def command(self, *args, **kwargs):
        return self.config.link_lib(*args, **kwargs)

class BytecodeExecutable(_Linker):
    default_config = 'fbuild.builders.ocaml.config_bytecode'

    def command(self, *args, **kwargs):
        return self.config.link_exe(*args, **kwargs)

class NativeExecutable(_Linker):
    default_config = 'fbuild.builders.ocaml.config_native'

    def command(self, *args, **kwargs):
        return self.config.link_exe(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(_Linker):
    '''
    Choose the native compiler if it is available, or if not available, fall
    back to the bytecode compiler.
    '''

    @property
    def config(self):
        c = super().config
        if c is not None:
            return c

        try:
            return env.cache('fbuild.builders.ocaml.config_native')
        except ConfigFailed:
            return env.cache('fbuild.builders.ocaml.config_bytecode')

    def compiler(self, *args, **kwargs):
        return self.config.compile(*args, **kwargs)

class Library(_Linker):
    def command(self, *args, **kwargs):
        return self.config.link_lib(*args, **kwargs)

class Executable(_Linker):
    def command(self, *args, **kwargs):
        return self.config.link_exe(*args, **kwargs)

# -----------------------------------------------------------------------------

class Ocamllex(packages.SimplePackage):
    default_config = 'fbuild.builders.ocaml.config_ocamllex'

    def command(self, *args, **kwargs):
        return self.config(*args, **kwargs)

class Ocamlyacc(packages.SimplePackage):
    default_config = 'fbuild.builders.ocaml.config_ocamlyacc'

    def command(self, *args, **kwargs):
        return self.config(*args, **kwargs)
