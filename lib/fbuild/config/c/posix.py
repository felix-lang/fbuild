"""fbuild.config.c.posix extends fbuild.config.c.posix04 to expose cross
platform flags and libraries, and exposes many common extensions."""

import fbuild.config.c as c
from fbuild.config.c.posix04 import *

# ------------------------------------------------------------------------------

class dlfcn_h(dlfcn_h):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Linux needs to link against libdl for dl* support.
        if 'linux' in self.platform:
            self.external_libs.append('dl')

class pthread_h(pthread_h):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'linux' in self.platform:
            self.external_libs.append('pthread')

        # Solaris needs to link against librt for posix support.
        elif 'solaris' in self.platform:
            self.external_libs.append('rt')

class stdlib_h(stdlib_h):
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

class string_h(string_h):
    @c.cacheproperty
    def strerror_r(self):
        if not self.header:
            return None

        # Some implementations return a char* of the message.
        fbuild.logger.check("checking strerror_r in 'string.h'")

        if self.builder.try_run('''
                #include <string.h>
                int main() {
                    char b[50];
                    int r = strerror_r(0, b, 50);
                    return r == 0 ? 0 : 1;
                }
                '''):
            fbuild.logger.passed()
            return c.Function('int', 'int', 'char*', 'size_t')

        if self.builder.try_run('''
                #include <string.h>
                int main() {
                    char b[50];
                    char* r = strerror_r(0, b, 50);
                    return 0;
                }
                '''):
            fbuild.logger.passed()
            return c.Function('char*', 'int', 'char*', 'size_t')

        fbuild.logger.failed()

class sys_mman_h(sys_mman_h):
    header = 'sys/mman.h'

    MADV_DOFORK = c.macro_test()
    MADV_DONTFORK = c.macro_test()
    MADV_DONTNEED = c.macro_test()
    MADV_FREE = c.macro_test()
    MADV_NORMAL = c.macro_test()
    MADV_RANDOM = c.macro_test()
    MADV_REMOVE = c.macro_test()
    MADV_SEQUENTIAL = c.macro_test()
    MADV_WILLNEED = c.macro_test()
    MAP_32BIT = c.macro_test()
    MAP_ANON = c.macro_test()
    MAP_ANONYMOUS = c.macro_test()
    MAP_COPY = c.macro_test()
    MAP_DENYWRITE = c.macro_test()
    MAP_EXECUTABLE = c.macro_test()
    MAP_FILE = c.macro_test()
    MAP_GROWSDOWN = c.macro_test()
    MAP_HASSEMAPHORE = c.macro_test()
    MAP_LOCKED = c.macro_test()
    MAP_NOCACHE = c.macro_test()
    MAP_NOEXTEND = c.macro_test()
    MAP_NONBLOCK = c.macro_test()
    MAP_NORESERVE = c.macro_test()
    MAP_POPULATE = c.macro_test()
    MAP_RENAME = c.macro_test()
    MAP_SHARED = c.macro_test()
    MAP_TYPE = c.macro_test()
    MINCORE_INCORE = c.macro_test()
    MINCORE_MODIFIED = c.macro_test()
    MINCORE_MODIFIED_OTHER = c.macro_test()
    MINCORE_REFERENCED = c.macro_test()
    MINCORE_REFERENCED_OTHER = c.macro_test()
    MREMAP_FIXED = c.macro_test()
    MREMAP_MAYMOVE = c.macro_test()
    PROT_GROWSDOWN = c.macro_test()
    PROT_GROWSUP = c.macro_test()
    madvise = c.function_test('void*', 'size_t', 'int')
    mincore = c.function_test('int', 'const void*', 'size_t', 'char*')
    minherit = c.function_test('void*', 'size_t', 'int')

class sys_types_h(sys_types_h):
    header = 'sys/types.h'

    u_int32_t = c.type_test()
    u_int64_t = c.type_test()

class unistd_h(unistd_h):
    mkstemps = c.function_test('int', 'char*', 'int')
    mkdtemp = c.function_test('char*', 'char*')
