import fbuild.config.c as c

# ------------------------------------------------------------------------------

class libgen_h(c.Header):
    basename = c.function_test('char*', 'char*')
    dirname = c.function_test('char*', 'char*')

class stdlib_h(c.Header):
    ecvt = c.function_test('char*', 'double', 'int', 'int*', 'int*')
    fcvt = c.function_test('char*', 'double', 'int', 'int*', 'int*')
    gcvt = c.function_test('char*', 'double', 'int', 'char*')
    mktemp = c.function_test('char*', 'char*')

class strings_h(c.Header):
    bcmp = c.function_test('int', 'const void*', 'const void*', 'size_t')
    bcopy = c.function_test('void', 'const void*', 'void*', 'size_t',
        default_args=(0, 0, 0))
    bzero = c.function_test('void', 'void*', 'size_t')

class unistd_h(c.Header):
    brk = c.function_test('void*', 'void*')
    getwd = c.function_test('char*', 'char*', test='''
        #include <unistd.h>
        #include <sys/param.h>
        int main() {
            char arg[MAXPATHLEN];
            char* res = getwd(arg);
            return 0;
        }
        ''')
    sbrk = c.function_test('void*', 'intptr_t')
    ttyslot = c.function_test('int', 'void')
