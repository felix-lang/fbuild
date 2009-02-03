import fbuild.config.c as c
import fbuild.config.c.posix04 as posix04

# ------------------------------------------------------------------------------

class execinfo_h(c.Header):
    backtrace = c.function_test('int', 'void**', 'int', test='''
        #include <execinfo.h>
        int main() {
            void* callstack[128];
            int frames = backtrace(callstack, 128);
            char** strs = backtrace_symbols(callstack, frames);
            return 0;
        }
        ''')
    backtrace_symbols = c.function_test('char**', 'void* const*', 'int',
        test=backtrace.test)
    backtrace_symbols_fd = c.function_test('void', 'void* const*', 'int', 'int')

class stdlib_h(posix04.stdlib_h):
    mkdtemp = c.function_test('char*', 'char*')
    strtof = c.function_test('double', 'const char*', 'char**', test='''
        #include <stdlib.h>
        int main() {
            char* s1 = "15";
            char* s2 = "abc";
            char* endp;
            quad_t d = strtoq(s1, &endp);
            if (s1 != endp && *endp == '\0' && d == 15.0) {
                d = strtoq(s2, &endp);
                return s1 == endp || *endp != '\0' ? 0 : 1;
            }
            return 1;
        }
        ''')

class sys_dir_h(c.Header):
    header = 'sys/dir.h'

    DIR = c.type_test()

class sys_event_h(c.Header):
    header = 'sys/event.h'

    kqueue = c.function_test('int', 'void', test='''
        #include <sys/types.h>      // from the kqueue manpage
        #include <sys/event.h>      // kernel events
        #include <sys/time.h>       // timespec (kevent timeout)

        int main(int argc, char** argv) {
            int kq = kqueue();
            return (-1 == kq) ? 1 : 0;
        }
        ''')

class sys_ndir_h(c.Header):
    header = 'sys/ndir.h'

class sys_param_h(c.Header):
    header = 'sys/param.h'

class unistd_h(posix04.unistd_h):
    mkstemps = c.function_test('int', 'char*', 'int')
    mkdtemp = c.function_test('char*', 'char*')
