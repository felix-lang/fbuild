import fbuild.config.c as c

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
