import os
import io
import textwrap
import contextlib

from ...temp import tempdir
from ... import ExecutionError
from ... import builders

# -----------------------------------------------------------------------------

class Builder(builders.Builder):
    def compile(self, *args, **kwargs):
        pass


    def link_lib(self, *args, **kwargs):
        pass


    def link_exe(self, *args, **kwargs):
        pass


    @contextlib.contextmanager
    def tempfile(self,
            code='int main(int argc, char** argv) { return 0; }',
            headers=[],
            name='temp',
            suffix='.c'):
        src = io.StringIO()

        for header in headers: print('#include <%s>' % header, file=src)
        print('#ifdef __cplusplus', file=src)
        print('extern "C" {', file=src)
        print('#endif', file=src)
        print(textwrap.dedent(code), file=src)
        print('#ifdef __cplusplus', file=src)
        print('}', file=src)
        print('#endif', file=src)

        with tempdir() as dirname:
            name = os.path.join(dirname, name + suffix)
            with open(name, 'w') as f:
                print(src.getvalue(), file=f)

            yield name


    def check_header_exists(self, header,
            suffix='.c',
            quieter=1,
            **kwargs):
        try:
            with self.tempfile(headers=[header], suffix=suffix) as src:
                self.compile([src], quieter=quieter, **kwargs)
        except ExecutionError:
            return False
        else:
            return True


    def check_macro_defined(self, macro,
            headers=[],
            suffix='.c',
            quieter=1,
            **kwargs):
        code = '''
            #ifndef %s
            #error %s
            #endif
        ''' % (macro, macro)

        self.check(0, 'checking if %s is defined' % macro)
        try:
            with self.tempfile(code, headers=headers, suffix=suffix) as src:
                self.compile([src], quieter=quieter, **kwargs)
        except ExecutionError:
            self.log(0, 'yes', color='green')
            return False
        else:
            self.log(0, 'no', color='yellow')
            return True


    def try_tempfile_compile(self, code, headers=[], quieter=1, **kwargs):
        with self.tempfile(code, headers=headers) as src:
            try:
                self.compile([src], quieter=quieter)
            except ExecutionError:
                return False
            else:
                return True


    def try_tempfile_link_exe(self, code,
            headers=[],
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers=headers) as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                objects = self.compile([src], quieter=quieter, **cflags)
                self.link_exe(dst, objects, quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True


    def try_tempfile_run(self, code,
            headers=[],
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers=headers) as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                objects = self.compile([src], quieter=quieter, **cflags)
                exe = self.link_exe(dst, objects, quieter=quieter, **lflags)
                self.system.execute([exe], quieter=quieter)
            except ExecutionError:
                return False
            else:
                return True

# -----------------------------------------------------------------------------

def config_static(system, options, model=None, exe=None):
    import fbuild.builders.c.gcc
    return gcc.config_static(system)

def config_shared(system, options, model=None, exe=None):
    import fbuild.builders.c.gcc
    return gcc.config_shared(system)

# -----------------------------------------------------------------------------

def check_compiler(compiler):
    pass

def check_builder(builder):
    pass
