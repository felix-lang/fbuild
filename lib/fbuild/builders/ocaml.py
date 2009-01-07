"""
Implement builders for the ocaml programming language.

This builder is compatible with ocaml 3.10 and above.
"""

import collections
from functools import partial
from itertools import chain

import fbuild
import fbuild.db
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path
from fbuild.record import Record
from fbuild.temp import tempdir
from fbuild.builders import find_program, AbstractCompilerBuilder

# ------------------------------------------------------------------------------

class Ocamldep(fbuild.db.PersistentObject):
    """Use ocamldoc to generate dependencies for ocaml files."""

    def __init__(self, exe, module_flags=[]):
        self.exe = exe
        self.module_flags = module_flags

    @fbuild.db.cachemethod
    def modules(self, src:fbuild.db.SRC, *, flags=[]):
        """Calculate the modules this ocaml file depends on."""
        src = Path(src)

        cmd = [self.exe, '-modules']
        cmd.extend(self.module_flags)
        cmd.extend(flags)
        cmd.append(src)

        fbuild.logger.check(' * ' + self.exe, src, color='yellow')
        stdout, stderr = execute(cmd, quieter=1)

        # Parse the output and return the module dependencies.
        return stdout.decode().replace('\\\n', '').split(':')[1].split()

    def source_dependencies(self, src, *args, includes=(), **kwargs):
        """Compute the source files this ocaml file depends on."""
        deps = []

        def f(module, include):
            found = False
            for suffix in '.mli', '.ml':
                path = Path(module[0].lower() + module[1:] + suffix)
                if include is not None: path = include / path

                if path.exists():
                    found = True
                    deps.append(path)
            return found

        for module in self.modules(src, *args, **kwargs):
            if not f(module, None):
                for include in chain(includes):
                    f(module, include)

        if src.endswith('.ml'):
            mli = Path(src).replaceext('.mli')
            if mli.exists():
                deps.append(mli)

        return deps

    def all_source_dependencies(self, src, *args, includes=(), **kwargs):
        """Recursively compute all the source files this ocaml file depends
        on."""
        deps = set()
        def add(src):
            for dep in self.source_dependencies(src, *args,
                    includes=includes,
                    **kwargs):
                add(dep)
                deps.add(dep)

        add(src)

        return sorted(deps)

    def __str__(self):
        return self.exe

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.exe,
            self.module_flags)

    def __eq__(self, other):
        return isinstance(other, Ocamldep) and \
            self.exe == other.exe and \
            self.module_flags == other.module_flags

# ------------------------------------------------------------------------------

class Builder(AbstractCompilerBuilder):
    def __init__(self, ocamldep, exe, *,
            obj_suffix,
            lib_suffix,
            exe_suffix,
            includes=[],
            libs=[],
            pre_flags=[],
            flags=[],
            debug_flags=['-g']):
        super().__init__(src_suffix='.ml')

        self.ocamldep = ocamldep
        self.exe = exe
        self.obj_suffix = obj_suffix
        self.lib_suffix = lib_suffix
        self.exe_suffix = exe_suffix
        self.includes = includes
        self.libs = libs
        self.pre_flags = pre_flags
        self.flags = flags
        self.debug_flags = debug_flags

    # -------------------------------------------------------------------------

    def where(self):
        stdout, stderr = execute([self.exe, '-where'], quieter=1)
        return Path(stdout.decode().strip())

    # -------------------------------------------------------------------------

    def _run(self, dst, srcs, *,
            includes=[],
            libs=[],
            external_libs=[],
            pre_flags=[],
            flags=[],
            debug=False,
            custom=False,
            c_libs=[],
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        libs = tuple(chain(self.libs, external_libs, libs))

        # we need to make sure libraries are built first before we compile
        # the sources
        assert srcs or libs, "%s: no sources or libraries passed in" % dst

        dst = Path(dst).addroot(buildroot)
        dst.parent.makedirs()

        extra_srcs = []
        for lib in libs:
            if Path(lib).exists():
                extra_srcs.append(lib)
            else:
                extra_srcs.append(lib + self.lib_suffix)

        cmd = [self.exe]
        cmd.extend(self.pre_flags)
        cmd.extend(pre_flags)

        if debug:
            cmd.extend(self.debug_flags)

        includes = set(includes)
        includes.update(self.includes)
        includes.add(dst.parent)

        for i in sorted(includes):
            i = Path(i)
            if i.exists():
                cmd.extend(('-I', i))

        if custom:
            cmd.append('-custom')

        for lib in c_libs:
            if Path(lib).exists():
                cmd.extend(('-cclib', lib))
            else:
                cmd.extend(('-cclib', '-l' + lib))

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(('-o', dst))
        cmd.extend(extra_srcs)
        cmd.extend(srcs)

        execute(cmd, self.exe,
            '%s -> %s' % (' '.join(extra_srcs + srcs), dst),
            **kwargs)

        return dst

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, *args, **kwargs) -> fbuild.db.DST:
        """Compile an ocaml implementation or interface file and cache the
        results."""
        return self.uncached_compile(src, *args, **kwargs)

    def uncached_compile(self, src, dst=None, *args, **kwargs):
        """Compile an ocaml implementation or interface file without caching
        the results.  This is needed when compiling temporary files."""
        if src.endswith('.mli'):
            obj_suffix = '.cmi'
        else:
            obj_suffix = self.obj_suffix

        dst = Path(dst or src).replaceext(obj_suffix)

        return self._run(dst, [src],
            pre_flags=['-c'],
            color='green',
            *args, **kwargs)

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def link_lib(self, dst, srcs:fbuild.db.SRCS, *args,
            libs:fbuild.db.SRCS=[],
            **kwargs) -> fbuild.db.DST:
        """Compile all the L{srcs} and link into a library."""
        return self.uncached_link_lib(dst, srcs, *args, libs=libs, **kwargs)

    def uncached_link_lib(self, dst, *args,
            libs=[],
            external_libs=[],
            **kwargs):
        """Link compiled ocaml files into a library without caching the
        results.  This is needed when linking temporary files."""
        # ignore passed in libraries
        return self._link(dst + self.lib_suffix,
            pre_flags=['-a'], *args, **kwargs)

    @fbuild.db.cachemethod
    def link_exe(self, dst, srcs:fbuild.db.SRCS, *args,
            libs:fbuild.db.SRCS=[],
            **kwargs) -> fbuild.db.DST:
        """Compile all the L{srcs} and link into an executable."""
        return self.uncached_link_exe(dst, srcs, *args, libs=libs, **kwargs)

    def uncached_link_exe(self, dst, *args, **kwargs):
        """Link compiled ocaml files into an executable without caching the
        results.  This is needed when linking temporary files."""
        return self._link(dst + self.exe_suffix, *args, **kwargs)

    def _link(self, dst, srcs, *args, libs=[], **kwargs):
        """Actually link the sources."""
        # Filter out the .cmi files, such as when we're using ocamlyacc source
        # files.
        srcs = [src for src in srcs if not src.endswith('.cmi')]

        return self._run(dst, srcs, libs=libs, color='cyan', *args, **kwargs)

    # -------------------------------------------------------------------------

    def build_objects(self, srcs, *, includes=[], buildroot=None, **kwargs):
        """Compile all the L{srcs} in parallel."""
        # When a object has extra external dependencies, such as .cmx files
        # depending on library changes, we need to add the dependencies in
        # build_objects.  Unfortunately, the db doesn't know about these new
        # files and so it can't tell when a function really needs to be rerun.
        # So, we'll just not cache this function.
        buildroot = buildroot or fbuild.buildroot
        includes = set(includes)
        srcs = [Path(src) for src in srcs]
        for src in srcs:
            parent = src.parent
            if parent:
                includes.add(parent)
                includes.add(parent.addroot(fbuild.buildroot))

        kwargs['includes'] = includes
        kwargs['buildroot'] = buildroot

        return fbuild.scheduler.map_with_dependencies(
            partial(self.ocamldep.source_dependencies, includes=includes),
            partial(self.compile, includes=includes),
            srcs)

    def _build_link(self, function, dst, srcs, *,
            includes=[],
            cflags=[],
            ckwargs={},
            libs=[],
            external_libs=[],
            custom=False,
            c_libs=[],
            lflags=[],
            lkwargs={}):
        includes = set(includes)
        for lib in libs:
            if isinstance(lib, Path):
                includes.add(lib.parent)

        objs = self.build_objects(srcs,
            includes=includes,
            flags=cflags,
            **ckwargs)

        return function(dst, objs,
            includes=includes,
            libs=libs,
            external_libs=external_libs,
            custom=custom,
            c_libs=c_libs,
            flags=lflags,
            **lkwargs)

    @fbuild.db.cachemethod
    def build_lib(self, dst, srcs:fbuild.db.SRCS, *args,
            **kwargs) -> fbuild.db.DST:
        """Compile all the L{srcs} and link into a library."""
        return self._build_link(self.link_lib, dst, srcs, *args,
            **kwargs)

    @fbuild.db.cachemethod
    def build_exe(self, dst, srcs:fbuild.db.SRCS, *args,
            libs:fbuild.db.SRCS=[],
            **kwargs) -> fbuild.db.DST:
        """Compile all the L{srcs} and link into an executable."""
        return self._build_link(self.link_exe, dst, srcs, *args,
            libs=libs,
            **kwargs)

    # -------------------------------------------------------------------------

    def __str__(self):
        return self.exe

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.exe)

    def __eq__(self, other):
        return isinstance(other, Builder) and \
            self.exe == other.exe and \
            self.obj_suffix == other.obj_suffix and \
            self.lib_suffix == other.lib_suffix and \
            self.exe_suffix == other.exe_suffix and \
            self.debug_flags == other.debug_flags

# ------------------------------------------------------------------------------

class BytecodeBuilder(Builder):
    pass

# ------------------------------------------------------------------------------

class NativeBuilder(Builder):
    def __init__(self, ocamldep, ocamlopt, bytecode, *args,
            native_obj_suffix='.o',
            native_lib_suffix='.a',
            **kwargs):
        super().__init__(ocamldep, ocamlopt, *args, **kwargs)

        # We need the bytecode compiler to compile .mli files.
        self.bytecode = bytecode
        self.native_obj_suffix = native_obj_suffix
        self.native_lib_suffix = native_lib_suffix

    def compile(self, src, *args, **kwargs):
        """Compile an ocaml implementation or interface file and cache the
        results."""
        # If the src is an interface file, use the bytecode compiler to create
        # the .cmi file.
        if src.endswith('.mli'):
            return self.bytecode.compile(src, *args, **kwargs)

        # Since ocamlopt can inline code from other .cmx files, we need to make
        # sure we'll recompile if any of the source files we depend on change.
        includes = kwargs.get('includes', ())
        deps = self.ocamldep.all_source_dependencies(src, includes=includes)
        return super().compile.call_with_dependencies((src,) + args, kwargs,
            srcs=deps)

    def uncached_compile(self, src, *args, **kwargs):
        # If the src is an interface file, use the bytecode compiler to create
        # the .cmi file.
        if src.endswith('.mli'):
            return self.bytecode.uncached_compile(src, *args, **kwargs)
        return super().uncached_compile(src, *args, **kwargs)

    def link_lib(self, dst, srcs, *args, **kwargs):
        """Link compiled ocaml files into a library and cache the results."""
        libs = kwargs.get('libs', ())
        deps = list(libs)
        deps.extend(src.replaceext(self.native_obj_suffix) for src in srcs)
        deps.extend(lib.replaceext(self.native_lib_suffix) for lib in libs)
        return super().link_lib.call_with_dependencies(
            (dst, srcs) + args, kwargs, srcs=deps)

    def link_exe(self, dst, srcs, *args, **kwargs):
        """Link compiled ocaml files into a library and cache the results."""
        libs = kwargs.get('libs', ())
        deps = list(libs)
        deps.extend(src.replaceext(self.native_obj_suffix) for src in srcs)
        deps.extend(lib.replaceext(self.native_lib_suffix) for lib in libs)
        return super().link_exe.call_with_dependencies(
            (dst, srcs) + args, kwargs, srcs=deps)

    def build_lib(self, *args, **kwargs):
        libs = kwargs.get('libs', ())
        deps = [lib.replaceext(self.native_lib_suffix) for lib in libs]
        return super().build_lib.call_with_dependencies(args, kwargs, srcs=deps)

    def build_exe(self, *args, **kwargs):
        libs = kwargs.get('libs', ())
        deps = [lib.replaceext(self.native_lib_suffix) for lib in libs]
        return super().build_exe.call_with_dependencies(args, kwargs, srcs=deps)

# ------------------------------------------------------------------------------

def check_builder(builder):
    logger.check('checking if ocaml can make objects')
    if builder.try_compile():
        logger.passed()
    else:
        raise ConfigFailed('ocaml compiler failed')

    logger.check('checking if ocaml can make libraries')
    if builder.try_link_lib():
        logger.passed()
    else:
        raise ConfigFailed('ocaml lib linker failed')

    logger.check('checking if ocaml can make exes')
    if builder.try_link_exe():
        logger.passed()
    else:
        raise ConfigFailed('ocaml exe linker failed')

    logger.check('checking if ocaml can link lib to exe')
    with tempdir() as parent:
        src_lib = parent / 'lib.ml'
        with open(src_lib, 'w') as f:
            print('let x = 5;;', file=f)

        src_exe = parent / 'exe.ml'
        with open(src_exe, 'w') as f:
            print('print_int Lib.x;;', file=f)

        obj = builder.uncached_compile(src_lib, quieter=1)
        lib = builder.uncached_link_lib(parent / 'lib', [obj], quieter=1)

        obj = builder.uncached_compile(src_exe, quieter=1)
        exe = builder.uncached_link_exe(parent / 'exe', [obj], libs=[lib],
            quieter=1)

        try:
            stdout, stderr = execute([exe], quieter=1)
        except ExecutionError:
            raise ConfigFailed('failed to link ocaml lib to exe')
        else:
            if stdout != b'5':
               raise ConfigFailed('failed to link ocaml lib to exe')
            logger.passed()

# ------------------------------------------------------------------------------

class Ocamllex(fbuild.db.PersistentObject):
    def __init__(self, exe, flags=[]):
        self.exe = exe
        self.flags = flags

    @fbuild.db.cachemethod
    def __call__(self, src:fbuild.db.SRC, *,
            flags=[],
            buildroot=None) -> fbuild.db.DST:
        buildroot = buildroot or fbuild.buildroot
        dst = src.replaceext('.ml').addroot(buildroot)
        dst.parent.makedirs()

        cmd = [self.exe]
        cmd.extend(('-o', dst))
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(src)

        execute(cmd, self.exe,
            '%s -> %s' % (src, dst),
            color='yellow')

        return dst

    def __str__(self):
        return self.exe

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.exe, self.flags)

    def __eq__(self, other):
        return isinstance(other, Ocamllex) and \
            self.exe == other.exe and \
            self.flags == other.flags

@fbuild.db.caches
def config_ocamllex(exe=None, default_exes=['ocamllex.opt', 'ocamllex']):
    exe = exe or find_program(default_exes)

    return Ocamllex(exe)

# ------------------------------------------------------------------------------

class Ocamlyacc(fbuild.db.PersistentObject):
    def __init__(self, exe, flags=[]):
        self.exe = exe
        self.flags = flags

    @fbuild.db.cachemethod
    def __call__(self, src:fbuild.db.SRC, *,
            flags=[],
            buildroot=None) -> fbuild.db.DSTS:
        buildroot = buildroot or fbuild.buildroot
        # first, copy the src file into the buildroot
        src_buildroot = src.addroot(buildroot)
        dsts = (
            src_buildroot.replaceext('.ml'),
            src_buildroot.replaceext('.mli'),
        )

        if src != src_buildroot:
            src_buildroot.parent.makedirs()
            src.copy(src_buildroot)
            src = src_buildroot

        cmd = [self.exe]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(src)

        execute(cmd, self.exe, '%s -> %s' % (src, ' '.join(dsts)),
            color='yellow')

        return dsts

    def __str__(self):
        return self.exe

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.exe, self.flags)

    def __eq__(self, other):
        return isinstance(other, Ocamlyacc) and \
            self.exe == other.exe and \
            self.flags == other.flags

@fbuild.db.caches
def config_ocamlyacc(exe=None, default_exes=['ocamlyacc.opt', 'ocamlyacc'],
        **kwargs):
    exe = exe or find_program(default_exes)

    return Ocamlyacc(exe, **kwargs)

# ------------------------------------------------------------------------------

class BothBuilders(AbstractCompilerBuilder):
    Tuple = collections.namedtuple('Tuple', 'bytecode native')

    def __init__(self, ocamldep, bytecode, native):
        self.ocamldep = ocamldep
        self.bytecode = bytecode
        self.native = native

    # --------------------------------------------------------------------------

    def compile(self, *args, **kwargs):
        """Compile an ocaml implementation or interface file and cache the
        results.  This returns a tuple of the generated bytecode and native
        object filename."""
        # The sub-compilers will handle the actual caching.
        return self._compile(
            self.bytecode.compile,
            self.native.compile)

    def uncached_compile(self, *args, **kwargs):
        """Compile an ocaml implementation or interface file without caching
        the results.  This is needed when compiling temporary files. This
        returns a tuple of the generated bytecode and native object
        filename."""
        return self._compile(
            self.bytecode.uncached_compile,
            self.native.uncached_compile)

    def link_lib(self, *args, **kwargs):
        """Link compiled ocaml files into a bytecode and native library and
        cache the results."""
        # The sub-linkers will handle the actual caching.
        return self._link(
            self.bytecode.link_lib,
            self.native.link_lib)

    def uncached_link_lib(self, *args, **kwargs):
        """Link compiled ocaml files into a bytecode and native library without
        caching the results.  This is needed when linking temporary files."""
        return self._link(
            self.bytecode.uncached_link_lib,
            self.native.uncached_link_lib)

    def link_exe(self, *args, **kwargs):
        """Link compiled ocaml files into a bytecode and native executable and
        cache the results."""
        # The sub-linkers will handle the actual caching.
        return self._link(self.bytecode.link_exe, self.native.link_exe)

    def uncached_link_exe(self, *args, **kwargs):
        """Link compiled ocaml files into a bytecode and native executable
        without caching the results.  This is needed when linking temporary
        files."""
        return self._link(
            self.bytecode.uncached_link_exe,
            self.native.uncached_link_exe)

    # --------------------------------------------------------------------------

    def build_objects(self, srcs, *args, **kwargs):
        """Compile all the L{srcs} in parallel."""
        return \
            self.bytecode.build_objects(srcs, *args, **kwargs) + \
            self.native.build_objects(srcs, *args, **kwargs)

    def build_lib(self, *args, **kwargs):
        """Compile and link ocaml source files into a bytecode and native
        library."""
        return self._link(
            self.bytecode.build_lib,
            self.native.build_lib, *args, **kwargs)

    def build_exe(self, *args, **kwargs):
        """Compile and link ocaml source files into a bytecode and native
        executable."""
        return self._link(
            self.bytecode.build_exe,
            self.native.build_exe, *args, **kwargs)

    # --------------------------------------------------------------------------

    def _compile(self, bcompile, ncompile, *args, **kwargs):
        """Actually compile the source using the bytecode and native
        compilers."""
        bobj = bcompile(*args, **kwargs)

        if src.endswith('.mli'):
            # We only need to generate the interface once.
            nobj = bobj
        else:
            nobj = ncompile(*args, **kwargs)

        return self.Tuple(bobj, nobj)

    def _link(self, blink, nlink, dst, srcs, *args, libs=[], **kwargs):
        """Actually link the sources using the bytecode and native compilers."""
        # the first item is the bytecode object, the second the native one
        bsrcs = [(s[0] if isinstance(s, self.Tuple) else s) for s in srcs]
        nsrcs = [(s[1] if isinstance(s, self.Tuple) else s) for s in srcs]

        # the first item is the bytecode lib, the second the native one
        blibs = [(l[0] if isinstance(l, self.Tuple) else l) for l in libs]
        nlibs = [(l[1] if isinstance(l, self.Tuple) else l) for l in libs]

        blib = blink(dst, bsrcs, *args, libs=blibs, **kwargs)
        nlib = nlink(dst, nsrcs, *args, libs=nlibs, **kwargs)

        return self.Tuple(blib, nlib)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def config_ocaml(*,
        ocamldep=None,
        default_ocamldep=['ocamldep.opt', 'ocamldep'],
        ocamlc=None,
        default_ocamlc=['ocamlc.opt', 'ocamlc'],
        ocamlopt=None,
        default_ocamlopt=['ocamlopt.opt', 'ocamlopt']):
    ocamlc = ocamlc or find_program(default_ocamlc)
    ocamlopt = ocamlopt or find_program(default_ocamlopt)

    ocamldep = Ocamldep(ocamldep or find_program(default_ocamldep))
    bytecode = BytecodeBuilder(ocamldep, ocamlc,
        obj_suffix='.cmo',
        lib_suffix='.cma',
        exe_suffix='')
    native = NativeBuilder(ocamldep, ocamlopt, bytecode,
        obj_suffix='.cmx',
        lib_suffix='.cmxa',
        exe_suffix='')

    check_builder(bytecode)
    check_builder(native)

    return BothBuilders(ocamldep, bytecode, native)

def config(*, ocamllex=None, ocamlyacc=None, **kwargs):
    return Record(
        ocaml=config_ocaml(**kwargs),
        ocamllex=config_ocamllex(ocamllex),
        ocamlyacc=config_ocamlyacc(ocamlyacc),
    )
