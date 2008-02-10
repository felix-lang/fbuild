import os
import textwrap
import contextlib

from fbuild import logger, execute, ConfigFailed, ExecutionError
import fbuild.temp
from fbuild.path import make_path, glob_paths

# -----------------------------------------------------------------------------

class Builder:
    def __init__(self, exe, *,
            obj_suffix,
            lib_suffix,
            exe_suffix,
            debug_flags=['-g']):
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
            buildroot=fbuild.buildroot,
            **kwargs):
        # we need to make sure libraries are built first before we compile
        # the sources
        assert srcs or libs

        dst = make_path(dst, root=buildroot)
        fbuild.path.make_dirs(os.path.dirname(dst))

        extra_srcs = []
        for lib in libs:
            if os.path.exists(lib):
                extra_srcs.append(lib)
            else:
                extra_srcs.append(lib + self.lib_suffix)

        cmd = [self.exe]
        cmd.extend(pre_flags)

        if debug:
            cmd.extend(self.debug_flags)

        for i in includes:
            cmd.extend(('-I', i))

        d = os.path.dirname(dst)
        if d not in includes:
            cmd.extend(('-I', d))

        cmd.extend(flags)
        cmd.extend(('-o', dst))
        cmd.extend(extra_srcs)
        cmd.extend(srcs)

        from fbuild import execute
        execute(cmd, self.exe,
            '%s -> %s' % (' '.join(extra_srcs + srcs), dst),
            **kwargs)

        return dst

    def compile_implementation(self, src, dst=None, *args, **kwargs):
        src = make_path(fbuild.scheduler.evaluate(src))

        if dst is None:
            dst = os.path.splitext(src)[0] + self.obj_suffix

        return self._run(dst, [src],
            pre_flags=['-c'],
            color='green',
            *args, **kwargs)

    def compile_interface(self, src, dst=None, *args, **kwargs):
        src = make_path(fbuild.scheduler.evaluate(src))

        if dst is None:
            dst = os.path.splitext(src)[0] + '.cmi'

        return self._run(dst, [src],
            pre_flags=['-c'],
            color='green',
            *args, **kwargs)

        return obj

    def compile(self, src, *args, **kwargs):
        src = make_path(fbuild.scheduler.evaluate(src))
        if os.path.exists(src + 'i'):
            interface = self.compile_interface(src + 'i', *args, **kwargs)
        else:
            interface = os.path.splitext(src)[0] + '.cmi'

        return self.compile_implementation(src, *args, **kwargs)

    def link_lib(self, dst, srcs, *args, libs=[], **kwargs):
        libs = [fbuild.scheduler.evaluate(l) for l in libs]
        srcs = glob_paths(fbuild.scheduler.evaluate(s) for s in srcs)

        return self._run(dst + self.lib_suffix, srcs,
            libs=libs,
            pre_flags=['-a'],
            color='cyan',
            *args, **kwargs)

    def link_exe(self, dst, srcs, *args, libs=[], **kwargs):
        libs = [fbuild.scheduler.evaluate(l) for l in libs]
        srcs = glob_paths(fbuild.scheduler.evaluate(s) for s in srcs)

        return self._run(dst + self.exe_suffix, srcs,
            libs=libs,
            color='cyan',
            *args, **kwargs)

    def check_flags(self, flags=[]):
        if flags:
            logger.check('checking %s with %s' % (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        with fbuild.temp.tempfile('', '.ml') as src:
            try:
                self.compile(flags + [src],
                    quieter=1,
                    cwd=os.path.dirname(src))
            except ExecutionError:
                logger.failed()
                return False

        logger.passed()
        return True

    def try_compile(self, code='', quieter=1, **kwargs):
        with fbuild.temp.tempfile(code, '.ml') as src:
            try:
                self.compile(src, quieter=quieter, **kwargs)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_lib(self, code='', *,
            quieter=1,
            cflags={},
            lflags={}):
        with fbuild.temp.tempfile(code, '.ml') as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_lib(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_exe(self, code='', *,
            quieter=1,
            cflags={},
            lflags={}):
        with fbuild.temp.tempfile(code, '.ml') as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_exe(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def tempfile_run(self, code='', *,
            quieter=1,
            cflags={},
            lflags={}):
        with fbuild.temp.tempfile(code, '.ml') as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            obj = self.compile(src, quieter=quieter, **cflags)
            exe = self.link_exe(dst, [obj], quieter=quieter, **lflags)
            return execute([exe], quieter=quieter)

    def try_run(self, *args, **kwargs):
        try:
            self.tempfile_run(*args, **kwargs)
        except ExecutionError:
            return False
        else:
            return True

    def check_compile(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_compile(code, *args, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    def check_run(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_run(code, *args, **kwargs):
            logger.passsed('yes')
            return True
        else:
            logger.failed('no')
            return False

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
    with fbuild.temp.tempdir() as dirname:
        src_lib = os.path.join(dirname, 'lib.ml')
        with open(src_lib, 'w') as f:
            print('let x = 5;;', file=f)

        src_exe = os.path.join(dirname, 'exe.ml')
        with open(src_exe, 'w') as f:
            print('print_int Lib.x;;', file=f)

        obj = builder.compile(src_lib, quieter=1)
        lib = builder.link_lib(os.path.join(dirname, 'lib'), [obj],
            quieter=1)

        obj = builder.compile(src_exe, quieter=1)
        exe = builder.link_exe(os.path.join(dirname, 'exe'), [obj],
            libs=[lib],
            quieter=1)

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
    from fbuild.builders import MissingProgram, find_program
    exe = exe or find_program(default_exes)

    builder = Builder(exe, *args, **kwargs)

    check_builder(builder)

    return builder

def config_bytecode(conf,
        exe=None,
        default_exes=['ocamlc.opt', 'ocamlc'],
        **kwargs):
    conf.setdefault('ocaml', {})['bytecode'] = make_builder(exe, default_exes,
        obj_suffix='.cmo',
        lib_suffix='.cma',
        exe_suffix='',
        **kwargs)

def config_native(conf,
        exe=None,
        default_exes=['ocamlopt.opt', 'ocamlopt'],
        **kwargs):
    conf.setdefault('ocaml', {})['native'] = make_builder(exe, default_exes,
        obj_suffix='.cmx',
        lib_suffix='.cmxa',
        exe_suffix='',
        **kwargs)

# -----------------------------------------------------------------------------

def config_ocamllex(conf, exe=None):
    pass

def config_ocamlyacc(conf, exe=None):
    pass

# -----------------------------------------------------------------------------

def config(conf,
        ocamlc=None,
        ocamlopt=None,
        ocamllex=None,
        ocamlyacc=None):
    config_bytecode(conf, ocamlc)
    config_native(conf, ocamlopt)
    config_ocamllex(conf, ocamllex)
    config_ocamlyacc(conf, ocamlyacc)
