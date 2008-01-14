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
    def tempfile(self,
            code='int main(int argc, char** argv) { return 0; }',
            headers=[],
            name='temp'):
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

        self.check(0, 'checking if %s is defined' % macro)
        try:
            with self.tempfile(code, headers=headers) as src:
                self.compile([src], quieter=quieter, **kwargs)
        except fbuild.ExecutionError:
            self.log(0, 'yes', color='green')
            return False
        else:
            self.log(0, 'no', color='yellow')
            return True

    # -------------------------------------------------------------------------

    def try_tempfile_compile(self, code, headers=[], quieter=1, **kwargs):
        with self.tempfile(code, headers=headers) as src:
            try:
                self.compile([src], quieter=quieter)
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
    code = 'int main(int argc, char** argv) { return 0; }'
    builder.check(0, 'checking if compiler works')
    if builder.try_tempfile_compile(code):
        builder.log(0, 'ok', color='green')
    else:
        raise fbuild.ConfigFailed('compiler failed')


    code = 'int foo() { return 5; }'
    builder.check(0, 'checking if lib linker works')
    if builder.try_tempfile_link_lib(code):
        builder.log(0, 'ok', color='green')
    else:
        raise fbuild.ConfigFailed('lib linker failed')


    code = 'int main(int argc, char** argv) { return 0; }'
    builder.check(0, 'checking if exe linker works')
    if builder.try_tempfile_run(code):
        builder.log(0, 'ok', color='green')
    else:
        raise fbuild.ConfigFailed('exe linker failed')




def check_link_lib(builder):
    dirname = tempfile.mkdtemp()
    try:
        src_lib = _write_src(dirname, 'templib' + self.src_suffix,
            'void foo() { return; }'
        )

        src_exe = _write_src(dirname, 'tempexe' + self.src_suffix,
            'extern void foo();'
            'int main(int argc, char** argv) { foo(); return 0; }'
        )
        lib_obj = compiler(system, [src_lib], **kwargs)
        exe_obj = compiler(system, [src_exe], **kwargs)

        lib = link_lib(system, os.path.join(dirname, 'temp'), lib_obj, **kwargs)

        exe_kwargs = kwargs.copy()
        exe_kwargs.setdefault('libs', []).append(lib)

        exe = link_exe(system,
            os.path.join(dirname, 'temp'), exe_obj, **exe_kwargs)

        system.log.check(0, 'Checking lib linking')
        try:
            system.execute([exe])
        except fbuild.system.ExecutionError:
            system.log(0, 'failed', color='yellow')
        else:
            system.log(0, 'ok', color='green')
    finally:
        shutil.rmtree(dirname)

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

def config_builder(conf, make_builder, *, tests=[], **kwargs):
    builder = conf.configure('builder', make_builder, conf.system, **kwargs)

    for test in tests:
        conf.subconfigure('', test, builder)

    return builder
