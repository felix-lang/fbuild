import fbuild
from fbuild import ConfigFailed, ExecutionError, execute, logger
import fbuild.temp
from fbuild.path import Path, find_in_paths

# ------------------------------------------------------------------------------

class MissingProgram(ConfigFailed):
    def __init__(self, program=None):
        self.program = program

    def __str__(self):
        if self.program is None:
            return 'cannot find program'
        else:
            return 'cannot find "%s"' % self.program

# ------------------------------------------------------------------------------

def find_program(names):
    for name in names:
        logger.check('checking for program ' + name)

        if find_in_paths(name):
            logger.passed('ok %s' % name)
            return name
        else:
            logger.failed('not found')

    raise ConfigFailed('failed to find any of ' + str(names))

# ------------------------------------------------------------------------------

class AbstractCompilerBuilder:
    def __init__(self, *, src_suffix):
        self.src_suffix = src_suffix

    def compile(self, *args, **kwargs):
        raise NotImplementedError

    def link_lib(self, *args, **kwargs):
        raise NotImplementedError

    def link_exe(self, *args, **kwargs):
        raise NotImplementedError

    # --------------------------------------------------------------------------

    def tempfile(self, code):
        return fbuild.temp.tempfile(code, self.src_suffix)

    def try_compile(self, code='', *, quieter=1, **kwargs):
        with self.tempfile(code) as src:
            try:
                self.compile(src, quieter=quieter, **kwargs)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_lib(self, code='', *, quieter=1, ckwargs={}, lkwargs={}):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **ckwargs)
                self.link_lib(dst, [obj], quieter=quieter, **lkwargs)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_exe(self, code='', *, quieter=1, ckwargs={}, lkwargs={}):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **ckwargs)
                self.link_exe(dst, [obj], quieter=quieter, **lkwargs)
            except ExecutionError:
                return False
            else:
                return True

    def tempfile_run(self, code='', *, quieter=1, ckwargs={}, lkwargs={},
            **kwargs):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            obj = self.compile(src, quieter=quieter, **ckwargs)
            exe = self.link_exe(dst, [obj], quieter=quieter, **lkwargs)
            return execute([exe], quieter=quieter, **kwargs)

    def try_run(self, code='', quieter=1, **kwargs):
        try:
            self.tempfile_run(code, quieter=quieter, **kwargs)
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

    def check_link_lib(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_link_lib(code, *args, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    def check_link_exe(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_link_exe(code, *args, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    def check_run(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_run(code, *args, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

# ------------------------------------------------------------------------------

def substitute(src, dst, patterns, *, buildroot=None):
    '''
    L{substitute} replaces the patterns in the src and saves the changes into
    dst.
    '''

    buildroot = buildroot or fbuild.buildroot
    src = Path(src)
    dst = Path.replace_root(dst or src, buildroot)

    dst.parent.make_dirs()

    with open(src, 'r') as f:
        old_code = code = f.read()

    for key, value in patterns.items():
        code = code.replace(key, value)

    # write out only if the file has been modified
    if code != old_code:
        fbuild.logger.log(' * creating ' + dst, color='cyan')
        with open(dst, 'w') as f:
            f.write(code)
