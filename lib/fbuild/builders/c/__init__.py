import os
from fbuild import logger, execute, ConfigFailed, ExecutionError
import fbuild.temp
import fbuild.builders

# -----------------------------------------------------------------------------

class MissingHeader(ConfigFailed):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return 'missing header %r' % self.filename

# -----------------------------------------------------------------------------

class Builder:
    def __init__(self, *, src_suffix):
        self.src_suffix = src_suffix

    # -------------------------------------------------------------------------

    def compile(self, *args, **kwargs):
        raise NotImplemented

    def link_lib(self, *args, **kwargs):
        raise NotImplemented

    def link_exe(self, *args, **kwargs):
        raise NotImplemented

    # -------------------------------------------------------------------------

    def check_header_exists(self, header, *, **kwargs):
        logger.check('checking if header %r exists' % header)
        if self.try_compile(headers=[header], **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    def check_macro_exists(self, macro, *, **kwargs):
        code = '''
            #ifndef %s
            #error %s
            #endif
        ''' % (macro, macro)

        logger.check('checking if macro %r exists' % macro)
        if self.try_compile(code, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    def check_type_exists(self, typename, *, **kwargs):
        code = '%s x;' % typename

        logger.check('checking if type %r exists' % typename)
        if self.try_compile(code, **kwargs):
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False

    # -------------------------------------------------------------------------

    def tempfile(self, code=None, headers=[], *args, **kwargs):
        code = code or 'int main(int argc, char** argv) { return 0; }'
        headers = ['#include <%s>' % h for h in headers]
        return fbuild.temp.tempfile('\n'.join(headers + [code]),
            self.src_suffix, *args, **kwargs)

    def try_compile(self, code=None, headers=[], *,
            quieter=1,
            **kwargs):
        with self.tempfile(code, headers) as src:
            try:
                self.compile(src, quieter=quieter, **kwargs)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_lib(self, code=None, headers=[], *,
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers) as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_lib(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def try_link_exe(self, code=None, headers=[], *,
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers) as src:
            dst = os.path.join(os.path.dirname(src), 'temp')
            try:
                obj = self.compile(src, quieter=quieter, **cflags)
                self.link_exe(dst, [obj], quieter=quieter, **lflags)
            except ExecutionError:
                return False
            else:
                return True

    def tempfile_run(self, code=None, headers=[], *,
            quieter=1,
            cflags={},
            lflags={}):
        with self.tempfile(code, headers) as src:
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
            logger.passed('yes')
            return True
        else:
            logger.failed('no')
            return False


def make_builder(Compiler, LibLinker, ExeLinker,
        src_suffix, obj_suffix,
        lib_prefix, lib_suffix,
        exe_suffix,
        compile_flags=[],
        lib_link_flags=[],
        exe_link_flags=[]):
    builder = Builder(src_suffix,
        Compiler(suffix=obj_suffix),
        LibLinker(
            prefix=lib_prefix,
            suffix=lib_suffix,
            lib_prefix=lib_prefix,
            lib_suffix=lib_suffix),
        ExeLinker(
            suffix=exe_suffix,
            lib_prefix=lib_prefix,
            lib_suffix=lib_suffix))

    check_builder(builder)

    return builder

# -----------------------------------------------------------------------------

def check_builder(builder):
    logger.check('checking if can make objects')
    if builder.try_compile():
        logger.passed()
    else:
        raise ConfigFailed('compiler failed')

    logger.check('checking if can make libraries')
    if builder.try_link_lib('int foo() { return 5; }'):
        logger.passed()
    else:
        raise ConfigFailed('lib linker failed')

    logger.check('checking if can make exes')
    if builder.try_run():
        logger.passed()
    else:
        raise ConfigFailed('exe linker failed')

    logger.check('Checking if can link lib to exe')
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

        obj = builder.compile(src_lib, quieter=1)
        lib = builder.link_lib(os.path.join(dirname, 'temp'), [obj],
            quieter=1)

        obj = builder.compile(src_exe, quieter=1)
        exe = builder.link_exe(os.path.join(dirname, 'temp'), [obj],
            libs=[lib],
            quieter=1)

        try:
            stdout, stderr = execute([exe], quieter=1)
        except ExecutionError:
            raise ConfigFailed('failed to link lib to exe')
        else:
            if stdout != b'5\n':
                raise ConfigFailed('failed to link lib to exe')
            logger.passed()

# -----------------------------------------------------------------------------

def config_compile_flags(builder, flags):
    logger.check('checking if "%s" supports %s' % (builder.compiler, flags))

    if builder.try_tempfile_compile(flags=flags):
        logger.passed()
        return True

    logger.failed()
    return False

# -----------------------------------------------------------------------------

def check_compiler(compiler, suffix):
    logger.check('checking if "%s" can make objects' % compiler)

    with compiler.tempfile(suffix=suffix) as f:
        try:
            compiler([f], quieter=1)
        except ExecutionError as e:
            raise ConfigFailed('compiler failed') from e

    logger.passed()

# -----------------------------------------------------------------------------

def config_little_endian(conf):
    code = '''
        #include <stdio.h>

        enum enum_t {e_tag};
        typedef void (*fp_t)(void);

        union endian_t {
            unsigned long x;
            unsigned char y[sizeof(unsigned long)];
        } endian;

        int main(int argc, char** argv) {
            endian.x = 1ul;
            printf("%d\\n", endian.y[0]);
            return 0;
        }
    '''

    logger.check('checking if little endian')
    try:
        stdout = 1 == int(conf['static'].tempfile_run(code)[0])
    except ExecutionError:
        logger.failed()
        raise ConfigFailed('failed to detect endianness')

    conf['little_endian'] = int(stdout) == 1
    logger.passed(conf['little_endian'])
