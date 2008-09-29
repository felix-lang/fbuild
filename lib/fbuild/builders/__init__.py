from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.temp import tempfile
from fbuild.path import find_in_paths, import_function

# -----------------------------------------------------------------------------

class MissingProgram(ConfigFailed):
    def __init__(self, program=None):
        self.program = program

    def __str__(self):
        if self.program is None:
            return 'cannot find program'
        else:
            return 'cannot find "%s"' % self.program

# -----------------------------------------------------------------------------

def find_program(names):
    for name in names:
        logger.check('checking for program ' + name)

        if find_in_paths(name):
            logger.passed('ok %s' % name)
            return name
        else:
            logger.failed('not found')

    raise ConfigFailed('failed to find any of ' + str(names))

# -----------------------------------------------------------------------------

class AbstractCompilerBuilder:
    def __init__(self, *, src_suffix):
        self.src_suffix = src_suffix

    def compile(self, *args, **kwargs):
        raise NotImplemented

    def link_lib(self, *args, **kwargs):
        raise NotImplemented

    def link_exe(self, *args, **kwargs):
        raise NotImplemented

    # -------------------------------------------------------------------------

    def try_compile(self, code='', *, quieter=1, **kwargs):
        with tempfile(code, self.src_suffix) as src:
            try:
                self.compile(src, quieter=quieter, **kwargs)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_lib(self, code='', *, quieter=1, cflags={}, lflags={}):
        with tempfile(code, self.src_suffix) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_lib(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_exe(self, code='', *, quieter=1, cflags={}, lflags={}):
        with tempfile(code, self.src_suffix) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_exe(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def tempfile_run(self, code='', *, quieter=1, cflags={}, lflags={}):
        with tempfile(code, self.src_suffix) as src:
            dst = src.parent / 'temp'
            obj = self.compile(src, quieter=quieter, **cflags)
            exe = self.link_exe(dst, [obj], quieter=quieter, **lflags)
            return execute([exe], quieter=quieter)

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

    def check_run(self, code, msg, *args, **kwargs):
        logger.check(msg)
        if self.try_run(code, *args, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False
