import os
import io
import textwrap
import contextlib

import fbuild
import fbuild.temp
import fbuild.builders

# -----------------------------------------------------------------------------

class Builder(fbuild.builders.Builder):
    yaml_state = ('compiler', 'lib_linker', 'exe_linker', 'src_suffix')

    def __init__(self, system, src_suffix, compiler, lib_linker, exe_linker):
        super().__init__(system)

        self.src_suffix = src_suffix
        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

    # -------------------------------------------------------------------------

    def compile(self, *args, **kwargs):
        return self.compiler(*args, **kwargs)


    def link_lib(self, *args, **kwargs):
        return self.lib_linker(*args, **kwargs)


    def link_exe(self, *args, **kwargs):
        return self.exe_linker(*args, **kwargs)

    # -------------------------------------------------------------------------

    @contextlib.contextmanager
    def tempfile(self, code=None, headers=[], name='temp'):
        code = code or 'int main(int argc, char** argv) { return 0; }'
        src = io.StringIO()

        for header in headers: print('#include <%s>' % header, file=src)
        print('#ifdef __cplusplus', file=src)
        print('extern "C" {', file=src)
        print('#endif', file=src)
        print(textwrap.dedent(code), file=src)
        print('#ifdef __cplusplus', file=src)
        print('}', file=src)
        print('#endif', file=src)

        with fbuild.temp.tempdir() as dirname:
            name = os.path.join(dirname, name + self.src_suffix)
            with open(name, 'w') as f:
                print(src.getvalue(), file=f)

            yield name

    # -------------------------------------------------------------------------

    def check_header_exists(self, header,
            suffix='.c',
            quieter=1,
            **kwargs):
        try:
            with self.tempfile(headers=[header]) as src:
                self.compile([src], quieter=quieter, **kwargs)
        except fbuild.ExecutionError:
            return False
        else:
            return True


    def check_macro_defined(self, macro,
            headers=[],
            quieter=1,
            **kwargs):
        code = '''
            #ifndef %s
            #error %s
            #endif
        ''' % (macro, macro)

        self.check('checking if "%s" is defined' % macro)
        try:
            with self.tempfile(code, headers=headers) as src:
                self.compile([src], quieter=quieter, **kwargs)
        except fbuild.ExecutionError:
            self.log('yes', color='green')
            return False
        else:
            self.log('no', color='yellow')
            return True

    # -------------------------------------------------------------------------

    def try_tempfile_compile(self, code=None, headers=[], quieter=1, **kwargs):
        with self.tempfile(code, headers=headers) as src:
            try:
                self.compile([src], quieter=quieter, **kwargs)
            except fbuild.ExecutionError:
                return False
            else:
                return True


    def try_tempfile_link_lib(self, code,
            headers=[],
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers=headers) as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                objects = self.compile([src], quieter=quieter, **cflags)
                self.link_lib(dst, objects, quieter=quieter, **lflags)
            except fbuild.ExecutionError:
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
            except fbuild.ExecutionError:
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
            except fbuild.ExecutionError:
                return False
            else:
                return True

    # -------------------------------------------------------------------------

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__,
            self.compiler,
            self.lib_linker,
            self.exe_linker,
        )

# -----------------------------------------------------------------------------

def check_builder(builder):
    builder.check('checking if "%s" can make objects' % builder.compiler)
    code = 'int main(int argc, char** argv) { return 0; }'
    if builder.try_tempfile_compile(code):
        builder.log('ok', color='green')
    else:
        raise fbuild.ConfigFailed('compiler failed')


    builder.check('checking if "%s" can make libraries' % builder.lib_linker)
    code = 'int foo() { return 5; }'
    if builder.try_tempfile_link_lib(code):
        builder.log('ok', color='green')
    else:
        raise fbuild.ConfigFailed('lib linker failed')


    builder.check('checking if "%s" can make exes' % builder.exe_linker)
    code = 'int main(int argc, char** argv) { return 0; }'
    if builder.try_tempfile_run(code):
        builder.log('ok', color='green')
    else:
        raise fbuild.ConfigFailed('exe linker failed')


    builder.check('Checking linking lib to exe')
    with fbuild.temp.tempdir() as dirname:
        src_lib = os.path.join(dirname, 'templib' + builder.src_suffix)
        with open(src_lib, 'w') as f:
            print('int foo() { return 5; }', file=f)

        src_exe = os.path.join(dirname, 'tempexe' + builder.src_suffix)
        with open(src_exe, 'w') as f:
            print('#include <stdio.h>', file=f)
            print('extern int foo();', file=f)
            print('int main(int argc, char** argv) {', file=f)
            print('  printf("%d\\n", foo());', file=f)
            print('  return 0;', file=f)
            print('}', file=f)


        objs = builder.compile([src_lib], quieter=1)
        lib = builder.link_lib(os.path.join(dirname, 'temp'), objs, quieter=1)

        objs = builder.compile([src_exe], quieter=1)
        exe = builder.link_exe(os.path.join(dirname, 'temp'), objs,
            libs=[lib],
            quieter=1)

        try:
            stdout, stderr = builder.system.execute([exe], quieter=1)
        except fbuild.system.ExecutionError:
            raise fbuild.ConfigFailed('failed to link lib to exe')
        else:
            if stdout != b'5\n':
                raise fbuild.ConfigFailed('failed to link lib to exe')
            builder.log('ok', color='green')

# -----------------------------------------------------------------------------

def make_builder(system, Compiler, LibLinker, ExeLinker,
        src_suffix, obj_suffix,
        lib_prefix, lib_suffix,
        exe_suffix,
        compile_flags=[],
        lib_link_flags=[],
        exe_link_flags=[]):
    builder = Builder(system, src_suffix,
        Compiler(system,
            suffix=obj_suffix,
        ),
        LibLinker(system,
            prefix=lib_prefix,
            suffix=lib_suffix,
            lib_prefix=lib_prefix,
            lib_suffix=lib_suffix,
        ),
        ExeLinker(system,
            suffix=exe_suffix,
            lib_prefix=lib_prefix,
            lib_suffix=lib_suffix,
        ),
    )

    check_builder(builder)

    return builder

# -----------------------------------------------------------------------------

def config_builder(conf, make_builder, *,
        tests=[],
        optional_tests=[],
        **kwargs):
    builder = conf.configure('builder', make_builder, conf.system, **kwargs)

    for test in tests:
        conf.subconfigure('', test, builder)

    for test in optional_tests:
        try:
            conf.subconfigure('', test, builder)
        except fbuild.ConfigFailed as e:
            pass

    return builder

# -----------------------------------------------------------------------------

def config_compile_flags(builder, flags):
    builder.check('checking if "%s" supports %s' % (builder, flags))

    if builder.try_tempfile_compile(flags=flags):
        builder.log('ok', color='green')
        return True

    builder.log('failed', color='yellow')
    return False
