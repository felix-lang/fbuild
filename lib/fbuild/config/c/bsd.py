import fbuild.config.c as c
import fbuild.config.c.posix04 as posix04

# ------------------------------------------------------------------------------

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

class sys_mman_h(posix04.sys_mman_h):
    MAP_ANON = c.macro_test()
    MAP_COPY = c.macro_test()
    MAP_HASSEMAPHORE = c.macro_test()
    MAP_NOCACHE = c.macro_test()
    MAP_NOEXTEND = c.macro_test()
    MAP_NORESERVE = c.macro_test()
    MAP_RENAME = c.macro_test()
    MADV_NORMAL = c.macro_test()
    MADV_RANDOM = c.macro_test()
    MADV_SEQUENTIAL = c.macro_test()
    MADV_WILLNEED = c.macro_test()
    MADV_DONTNEED = c.macro_test()
    MADV_FREE = c.macro_test()
    MINCORE_INCORE = c.macro_test()
    MINCORE_REFERENCED = c.macro_test()
    MINCORE_MODIFIED = c.macro_test()
    MINCORE_REFERENCED_OTHER = c.macro_test()
    MINCORE_MODIFIED_OTHER = c.macro_test()
    madvise = c.function_test('void*', 'size_t', 'int')
    mincore = c.function_test('int', 'const void*', 'size_t', 'char*')
    minherit = c.function_test('void*', 'size_t', 'int')
