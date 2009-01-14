import fbuild.config.c as c
import fbuild.config.c.posix04 as posix04

# ------------------------------------------------------------------------------

class sys_epoll_h(c.Header):
    header = 'sys/epoll.h'

    EPOLLIN = c.macro_test()
    EPOLLPRI = c.macro_test()
    EPOLLOUT = c.macro_test()
    EPOLLRDNORM = c.macro_test()
    EPOLLRDBAND = c.macro_test()
    EPOLLWRNORM = c.macro_test()
    EPOLLWRBAND = c.macro_test()
    EPOLLMSG = c.macro_test()
    EPOLLERR = c.macro_test()
    EPOLLHUP = c.macro_test()
    EPOLLONESHOT = c.macro_test()
    EPOLLET = c.macro_test()
    EPOLL_CTL_ADD = c.macro_test()
    EPOLL_CTL_DEL = c.macro_test()
    EPOLL_CTL_MOD = c.macro_test()
    epoll_data = c.struct_test(
        ('void*', 'ptr'),
        ('int', 'fd'),
        ('uint32_t', 'u32'),
        ('uint32_t', 'u64'))
    epoll_event = c.struct_test(
        ('uint32_t', 'events'),
        ('epoll_data_t', 'data'))
    epoll_create = c.function_test('int', 'int', test='''
        #include <sys/epoll.h>
        int main(int argc, char** argv) {
            int efd = epoll_create(20);
            return (-1 == efd) ? 1 : 0;
        }
        ''')
    epoll_ctl = c.function_test('int', 'int', 'int', 'struct epoll_event*')
    epoll_wait = c.function_test('int', 'int', 'struct epoll_event*', 'int', 'int')

class sys_mman_h(posix04.sys_mman_h):
    MADV_DOFORK = c.macro_test()
    MADV_DONTFORK = c.macro_test()
    MADV_DONTNEED = c.macro_test()
    MADV_NORMAL = c.macro_test()
    MADV_RANDOM = c.macro_test()
    MADV_REMOVE = c.macro_test()
    MADV_SEQUENTIAL = c.macro_test()
    MADV_WILLNEED = c.macro_test()
    MAP_32BIT = c.macro_test()
    MAP_ANON = c.macro_test()
    MAP_ANONYMOUS = c.macro_test()
    MAP_DENYWRITE = c.macro_test()
    MAP_EXECUTABLE = c.macro_test()
    MAP_GROWSDOWN = c.macro_test()
    MAP_LOCKED = c.macro_test()
    MAP_NONBLOCK = c.macro_test()
    MAP_NORESERVE = c.macro_test()
    MAP_POPULATE = c.macro_test()
    MAP_SHARED = c.macro_test()
    MAP_TYPE = c.macro_test()
    MREMAP_FIXED = c.macro_test()
    MREMAP_MAYMOVE = c.macro_test()
    PROT_GROWSDOWN = c.macro_test()
    PROT_GROWSUP = c.macro_test()
