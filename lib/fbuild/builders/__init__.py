import os

import fbuild
import fbuild.db
import fbuild.path
import fbuild.temp

# ------------------------------------------------------------------------------

class MissingProgram(fbuild.ConfigFailed):
    def __init__(self, program=None):
        self.program = program

    def __str__(self):
        if self.program is None:
            return 'cannot find program'
        else:
            return 'cannot find "%s"' % self.program

# ------------------------------------------------------------------------------

@fbuild.db.caches
def find_program(db, names, paths=None):
    """L{find_program} is a test that searches the paths for one of the
    programs in I{name}.  If one is found, it is returned.  If not, the next
    name in the list is searched for."""

    if paths is None:
        paths = os.environ['PATH'].split(os.pathsep)

    for name in names:
        fbuild.logger.check('looking for program ' + name)

        for path in paths:
            filename = os.path.join(path, name)
            if os.path.exists(filename):
                fbuild.logger.passed('ok %s' % name)
                return fbuild.path.Path(name)
        else:
            fbuild.logger.failed('not found')

    raise fbuild.ConfigFailed('failed to find %s' % ' '.join(names))

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
            except fbuild.ExecutionError:
                return False
            else:
                return True

    def try_link_lib(self, code='', *, quieter=1, ckwargs={}, lkwargs={}):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **ckwargs)
                self.link_lib(dst, [obj], quieter=quieter, **lkwargs)
            except fbuild.ExecutionError:
                return False
            else:
                return True

    def try_link_exe(self, code='', *, quieter=1, ckwargs={}, lkwargs={}):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            try:
                obj = self.compile(src, quieter=quieter, **ckwargs)
                self.link_exe(dst, [obj], quieter=quieter, **lkwargs)
            except fbuild.ExecutionError:
                return False
            else:
                return True

    def tempfile_run(self, code='', *, quieter=1, ckwargs={}, lkwargs={},
            **kwargs):
        with self.tempfile(code) as src:
            dst = src.parent / 'temp'
            obj = self.compile(src, quieter=quieter, **ckwargs)
            exe = self.link_exe(dst, [obj], quieter=quieter, **lkwargs)
            return fbuild.execute([exe], quieter=quieter, **kwargs)

    def try_run(self, code='', quieter=1, **kwargs):
        try:
            self.tempfile_run(code, quieter=quieter, **kwargs)
        except fbuild.ExecutionError:
            return False
        else:
            return True

    def check_compile(self, code, msg, *args, **kwargs):
        fbuild.logger.check(msg)
        if self.try_compile(code, *args, **kwargs):
            fbuild.logger.passed()
            return True
        else:
            fbuild.logger.failed()
            return False

    def check_link_lib(self, code, msg, *args, **kwargs):
        fbuild.logger.check(msg)
        if self.try_link_lib(code, *args, **kwargs):
            fbuild.logger.passed()
            return True
        else:
            fbuild.logger.failed()
            return False

    def check_link_exe(self, code, msg, *args, **kwargs):
        fbuild.logger.check(msg)
        if self.try_link_exe(code, *args, **kwargs):
            fbuild.logger.passed()
            return True
        else:
            fbuild.logger.failed()
            return False

    def check_run(self, code, msg, *args, **kwargs):
        fbuild.logger.check(msg)
        if self.try_run(code, *args, **kwargs):
            fbuild.logger.passed()
            return True
        else:
            fbuild.logger.failed()
            return False
