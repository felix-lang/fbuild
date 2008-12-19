from functools import partial

import fbuild
import fbuild.db
import fbuild.temp
import fbuild.builders
from fbuild import ConfigFailed, ExecutionError, execute, logger
from fbuild.path import Path

# ------------------------------------------------------------------------------

class MissingHeader(ConfigFailed):
    def __init__(self, filename=None):
        self.filename = filename

    def __str__(self):
        if self.filename is None:
            return 'missing header'
        else:
            return 'missing header %r' % self.filename

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.AbstractCompilerBuilder):
    @fbuild.db.cachemethod
    def build_objects(self, srcs:fbuild.db.srcs, **kwargs) -> fbuild.db.dsts:
        """Compile all of the passed in L{srcs} in parallel."""
        return fbuild.scheduler.map(partial(self.compile, **kwargs), srcs)

    # -------------------------------------------------------------------------

    def check_statement(self, name, statement, *,
            msg=None, headers=[], **kwargs):
        code = '''
            %s;
            int main() {
                %s
                return 0;
            }
        ''' % ('\n'.join('#include <%s>' % h for h in headers), statement)

        logger.check(msg or 'checking %r' % name)
        if self.try_compile(code, **kwargs):
            logger.passed()
            return True
        else:
            logger.failed()
            return False

    def check_statements(self, *items, msg='checking %r', **kwargs):
        results = set()
        for name, statement in items:
            if self.check_statement(name, statement, msg=msg % name, **kwargs):
                results.add(name)

        return results

    # -------------------------------------------------------------------------

    def check_header_exists(self, header, **kwargs):
        return self.check_statement(header, '',
            msg='checking if header %r exists' % header,
            headers=[header],
            **kwargs)

    def check_functions_exist(self, *args, **kwargs):
        return self.check_statements(*args,
            msg='checking if function %r exists', **kwargs)

    def check_macros_exist(self, *macros, **kwargs):
        code = '''
            #ifndef %s
            #error %s
            #endif
        '''

        return self.check_statements(
            *((m, code % (m, m)) for m in macros),
            msg='checking if macros %r exists', **kwargs)

    def check_types_exist(self, *types, **kwargs):
        items = []
        for name in types:
            try:
                name, statement = name
            except ValueError:
                name, statement = name, '%s t;' % name
            items.append((name, statement))

        return self.check_statements(*items,
            msg='checking if type %r exists', **kwargs)

# ------------------------------------------------------------------------------

def check_builder(builder):
    logger.check('checking if can make objects')
    if builder.try_compile('int main(int argc, char** argv) { return 0; }'):
        logger.passed()
    else:
        logger.failed('compiler failed')
        return False

    logger.check('checking if can make libraries')
    if builder.try_link_lib('int foo() { return 5; }'):
        logger.passed()
    else:
        logger.failed('lib linker failed')
        return False

    logger.check('checking if can make exes')
    if builder.try_run('int main(int argc, char** argv) { return 0; }'):
        logger.passed()
    else:
        logger.failed('exe linker failed')
        return False

    logger.check('checking if can link lib to exe')
    with fbuild.temp.tempdir() as dirname:
        src_lib = dirname / 'templib' + builder.src_suffix
        with open(src_lib, 'w') as f:
            print('int foo() { return 5; }', file=f)

        src_exe = dirname / 'tempexe' + builder.src_suffix
        with open(src_exe, 'w') as f:
            print('#include <stdio.h>', file=f)
            print('extern int foo();', file=f)
            print('int main(int argc, char** argv) {', file=f)
            print('  printf("%d\\n", foo());', file=f)
            print('  return 0;', file=f)
            print('}', file=f)

        obj = builder.uncached_compile(src_lib, quieter=1)
        lib = builder.uncached_link_lib(dirname / 'temp', [obj], quieter=1)
        obj = builder.uncached_compile(src_exe, quieter=1)
        exe = builder.uncached_link_exe(dirname / 'temp', [obj], libs=[lib],
                quieter=1)

        try:
            stdout, stderr = execute([exe], quieter=1)
        except ExecutionError:
            logger.failed('failed to link lib to exe')
            return False
        else:
            if stdout != b'5\n':
                logger.failed('failed to link lib to exe')
                return False
            logger.passed()

            return True

# ------------------------------------------------------------------------------

def config_compile_flags(builder, flags):
    logger.check('checking if "%s" supports %s' % (builder.compiler, flags))

    if builder.try_tempfile_compile(flags=flags):
        logger.passed()
        return True

    logger.failed()
    return False

# ------------------------------------------------------------------------------

def check_compiler(compiler, suffix):
    logger.check('checking if "%s" can make objects' % compiler)

    with compiler.tempfile(suffix=suffix) as f:
        try:
            compiler([f], quieter=1)
        except ExecutionError as e:
            raise ConfigFailed('compiler failed') from e

    logger.passed()

# ------------------------------------------------------------------------------

def config_little_endian(builder):
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
        stdout = 1 == int(builder.tempfile_run(code)[0])
    except ExecutionError:
        logger.failed()
        raise ConfigFailed('failed to detect endianness')

    little_endian = int(stdout) == 1
    logger.passed(little_endian)

    return little_endian
