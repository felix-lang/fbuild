import io
import textwrap

from fbuild import ConfigFailed, ExecutionError, buildroot, env, execute, logger
from fbuild.path import Path
from fbuild.record import Record
from fbuild.temp import tempdir
from fbuild.builders import find_program, AbstractCompilerBuilder

# -----------------------------------------------------------------------------

class Ocamldep:
    '''
    Use ocamldoc to generate dependencies for ocaml files.
    '''

    def __init__(self, exe, module_flags=[]):
        self.exe = exe
        self.module_flags = module_flags

    def __call__(self, src, *,
            includes=[],
            flags=[],
            buildroot=buildroot):
        dst = (src + '.depends').replace_root(buildroot)
        dst.parent.make_dirs()

        cmd = [self.exe]
        cmd.extend(self.module_flags)

        includes = set(includes)
        includes.add(src.parent)
        includes.add(dst.parent)

        for i in sorted(includes):
            i = Path(i)
            if i.exists():
                cmd.extend(('-I', i))

        cmd.extend(flags)
        cmd.append(src)

        with open(dst, 'w') as f:
            execute(cmd, self.exe, '%s -> %s' % (src, dst),
                stdout=f,
                color='yellow')

        suffixes = {'.cmo': '.ml', '.cmx': '.ml', '.cmi': '.mli'}
        d = {}
        with open(dst) as f:
            # we need to join lines ending in "\" together
            for line in io.StringIO(f.read().replace('\\\n', '')):
                name, *deps = line.split()

                # strip off the ':'
                name = Path(name[:-1]).replace_suffixes(suffixes)

                d[name] = Path.replace_all_suffixes(deps, suffixes)

        paths = []
        for path in d.get(src, []):
            if path not in paths:
                paths.append(path)

        return paths

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

def config_ocamldep(exe=None, default_exes=['ocamldep.opt', 'ocamldep']):
    exe = exe or find_program(default_exes)

    return Ocamldep(exe)

# -----------------------------------------------------------------------------

class Builder(AbstractCompilerBuilder):
    def __init__(self, exe, *,
            obj_suffix,
            lib_suffix,
            exe_suffix,
            debug_flags=['-g']):
        super().__init__(src_suffix='.ml')

        self.exe = exe
        self.obj_suffix = obj_suffix
        self.lib_suffix = lib_suffix
        self.exe_suffix = exe_suffix
        self.debug_flags = debug_flags

    def _run(self, dst, srcs, *,
            includes=[],
            libs=[],
            pre_flags=[],
            flags=[],
            debug=False,
            buildroot=buildroot,
            **kwargs):
        # we need to make sure libraries are built first before we compile
        # the sources
        assert srcs or libs, "%s: no sources or libraries passed in" % dst

        dst = Path.replace_root(dst, buildroot)
        dst.parent.make_dirs()

        extra_srcs = []
        for lib in libs:
            if Path.exists(lib):
                extra_srcs.append(lib)
            else:
                extra_srcs.append(lib + self.lib_suffix)

        cmd = [self.exe]
        cmd.extend(pre_flags)

        if debug:
            cmd.extend(self.debug_flags)

        includes = set(includes)
        includes.add(dst.parent)

        for i in sorted(includes):
            i = Path(i)
            if i.exists():
                cmd.extend(('-I', i))

        cmd.extend(flags)
        cmd.extend(('-o', dst))
        cmd.extend(extra_srcs)
        cmd.extend(srcs)

        execute(cmd, self.exe,
            '%s -> %s' % (' '.join(extra_srcs + srcs), dst),
            **kwargs)

        return dst

    def _compile(self, src, dst=None, *args, obj_suffix, **kwargs):
        if dst is None:
            dst = src.replace_ext(obj_suffix)

        return self._run(dst, [src],
            pre_flags=['-c'],
            color='green',
            *args, **kwargs)

    def compile_implementation(self, *args, **kwargs):
        return self._compile(obj_suffix=self.obj_suffix, *args, **kwargs)

    def compile_interface(self, *args, **kwargs):
        return self._compile(obj_suffix='.cmi', *args, **kwargs)

    def compile(self, src, *args, **kwargs):
        if src.endswith('.mli'):
            return self.compile_interface(src, *args, **kwargs)
        else:
            return self.compile_implementation(src, *args, **kwargs)

    def _link(self, dst, srcs, *args, libs=[], **kwargs):
        srcs = Path.glob_all(srcs)
        return self._run(dst, srcs, libs=libs, color='cyan', *args, **kwargs)

    def link_lib(self, dst, *args, libs=[], **kwargs):
        # ignore passed in libraries
        return self._link(dst + self.lib_suffix,
            pre_flags=['-a'], *args, **kwargs)

    def link_exe(self, dst, *args, **kwargs):
        return self._link(dst + self.exe_suffix, *args, **kwargs)

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

# -----------------------------------------------------------------------------

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

    logger.check('Checking if ocaml can link lib to exe')
    with tempdir() as parent:
        src_lib = parent / 'lib.ml'
        with open(src_lib, 'w') as f:
            print('let x = 5;;', file=f)

        src_exe = parent / 'exe.ml'
        with open(src_exe, 'w') as f:
            print('print_int Lib.x;;', file=f)

        obj = builder.compile(src_lib, quieter=1)
        lib = builder.link_lib(parent / 'lib', [obj], quieter=1)

        obj = builder.compile(src_exe, quieter=1)
        exe = builder.link_exe(parent / 'exe', [obj], libs=[lib], quieter=1)

        try:
            stdout, stderr = execute([exe], quieter=1)
        except ExecutionError:
            raise ConfigFailed('failed to link ocaml lib to exe')
        else:
            if stdout != b'5':
               raise ConfigFailed('failed to link ocaml lib to exe')
            logger.passed()

# -----------------------------------------------------------------------------

def make_builder(exe, default_exes, *args, **kwargs):
    builder = Builder(exe or find_program(default_exes), *args, **kwargs)
    check_builder(builder)

    return builder

def config_bytecode(
        exe=None,
        default_exes=['ocamlc.opt', 'ocamlc'],
        **kwargs):
    return make_builder(exe, default_exes,
        obj_suffix='.cmo',
        lib_suffix='.cma',
        exe_suffix='',
        **kwargs)

def config_native(
        exe=None,
        default_exes=['ocamlopt.opt', 'ocamlopt'],
        **kwargs):
    return make_builder(exe, default_exes,
        obj_suffix='.cmx',
        lib_suffix='.cmxa',
        exe_suffix='',
        **kwargs)

# -----------------------------------------------------------------------------

class Ocamllex:
    def __init__(self, exe, flags=[]):
        self.exe = exe
        self.flags = flags

    def __call__(self, src, *,
            flags=[],
            buildroot=buildroot):
        dst = src.replace_ext('.ml').replace_root(buildroot)
        dst.parent.make_dirs()

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

def config_ocamllex(exe=None, default_exes=['ocamllex.opt', 'ocamllex']):
    exe = exe or find_program(default_exes)

    return Ocamllex(exe)

# -----------------------------------------------------------------------------

class Ocamlyacc:
    def __init__(self, exe, flags=[]):
        self.exe = exe
        self.flags = flags

    def __call__(self, src, *,
            flags=[],
            buildroot=buildroot):
        # first, copy the src file into the buildroot
        src_buildroot = src.replace_root(buildroot)

        if src != src_buildroot:
            src_buildroot.parent.make_dirs()
            src.copy(src_buildroot)
            src = src_buildroot

        dst = src.replace_ext('.ml')

        cmd = [self.exe]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(src)

        execute(cmd, self.exe,
            '%s -> %s' % (src, dst),
            color='yellow')

        return (dst, dst + 'i')

    def __str__(self):
        return self.exe

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.exe, self.flags)

    def __eq__(self, other):
        return isinstance(other, Ocamlyacc) and \
            self.exe == other.exe and \
            self.flags == other.flags

def config_ocamlyacc(
        exe=None,
        default_exes=['ocamlyacc.opt', 'ocamlyacc']):
    exe = exe or find_program(default_exes)

    return Ocamlyacc(exe)

# -----------------------------------------------------------------------------

def config(*,
        ocamldep=None,
        ocamlc=None,
        ocamlopt=None,
        ocamllex=None,
        ocamlyacc=None):
    return Record(
        ocamldep=env.cache(config_ocamldep, ocamldep),
        bytecode=env.cache(config_bytecode, ocamlc),
        native=env.cache(config_native, ocamlopt),
        ocamllex=env.cache(config_ocamllex, ocamllex),
        ocamlyacc=env.cache(config_ocamlyacc, ocamlyacc),
    )
