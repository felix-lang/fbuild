import fbuild.config.c as c
import fbuild.config.c.c99 as c99

# ------------------------------------------------------------------------------

class aio_h(c.Header):
    aiocb = c.struct_test(
        ('int', 'aio_fildes'),
        ('off_t', 'aio_offset'),
        ('volatile void*', 'aio_buf'),
        ('size_t', 'aio_nbytes'),
        ('int', 'aio_reqprio'),
        ('struct sigevent', 'aio_sigevent'),
        ('int', 'aio_lio_opcode'))

    AIO_ALLDONE = c.variable_test()
    AIO_CANCELED = c.variable_test()
    AIO_NOTCANCELED = c.variable_test()
    LIO_NOP = c.variable_test()
    LIO_NOWAIT = c.variable_test()
    LIO_READ = c.variable_test()
    LIO_WAIT = c.variable_test()
    LIO_WRITE = c.variable_test()
    aio_cancel = c.function_test('int', 'int', 'struct aiocb*')
    aio_error = c.function_test('int', 'const struct aiocb*')
    aio_fsync = c.function_test('int', 'int, struct aiocb*')
    aio_read = c.function_test('int', 'struct aiocb*')
    aio_return = c.function_test('ssize_t', 'struct aiocb*')
    aio_suspend = c.function_test('int', 'const struct aiocb**', 'int', 'const struct timespec*')
    aio_write = c.function_test('int', 'struct aiocb*')
    lio_listio = c.function_test('int', 'int', 'struct aiocb* const', 'int', 'struct sigevent*')

# ------------------------------------------------------------------------------

class arpa_inet_h(c.Header):
    header = 'arpa/inet.h'

    in_port_t = c.type_test()
    in_addr_t = c.type_test()
    in_addr = c.struct_test(
        ('sa_family_t', 'sin_family'),
        ('in_port_t', 'sin_port'),
        ('struct in_addr', 'sin_addr'))
    INET_ADDRSTRLEN = c.macro_test()
    INET6_ADDRSTRLEN = c.macro_test()
    htonl = c.function_test('uint32_t', 'uint32_t')
    htons = c.function_test('uint16_t', 'uint16_t')
    ntohl = c.function_test('uint32_t', 'uint32_t')
    ntohs = c.function_test('uint16_t', 'uint16_t')
    inet_addr = c.function_test('in_addr_t', 'constchar*')
    inet_ntoa = c.function_test('char*', 'struct in_addr')
    inet_ntop = c.function_test('const char*', 'int', 'const void*', 'char*', 'socklen_t')
    inet_pton = c.function_test('int', 'int', 'const char*', 'void*')

# ------------------------------------------------------------------------------

assert_h = c99.assert_h
complex_h = c99.complex_h

# ------------------------------------------------------------------------------

class cpio_h(c.Header):
    C_IRUSR = c.variable_test()
    C_IWUSR = c.variable_test()
    C_IXUSR = c.variable_test()
    C_IRGRP = c.variable_test()
    C_IWGRP = c.variable_test()
    C_IXGRP = c.variable_test()
    C_IROTH = c.variable_test()
    C_IWOTH = c.variable_test()
    C_IXOTH = c.variable_test()
    C_ISUID = c.variable_test()
    C_ISGID = c.variable_test()
    C_ISVTX = c.variable_test()
    C_ISDIR = c.variable_test()
    C_ISFIFO = c.variable_test()
    C_ISREG = c.variable_test()
    C_ISBLK = c.variable_test()
    C_ISCHR = c.variable_test()
    C_ISCTG = c.variable_test()
    C_ISLNK = c.variable_test()
    C_ISSOCK = c.variable_test()
    MAGIC = c.variable_test()

# ------------------------------------------------------------------------------

class ctype_h(c99.ctype_h):
    isascii = c.function_test('int', 'int')
    toascii = c.function_test('int', 'int')
    _toupper = c.macro_test()
    _tolower = c.macro_test()

# ------------------------------------------------------------------------------

class dirent_h(c.Header):
    DIR = c.type_test()
    dirent = c.struct_test(
        ('ino_t', 'd_ino'),
        ('char*', 'd_name'))
    ino_t = c.type_test()
    closedir = c.function_test('int', 'DIR*', test='''
        #include <dirent.h>
        int main() {
            DIR* d = opendir(".");
            return d && closedir(d);
        }
        ''')
    opendir = c.function_test('DIR*', 'const char*', test=closedir.test)
    readdir = c.function_test('struct dirent*', 'DIR');
    readdir_r = c.function_test('int', 'DIR*', 'struct dirent*', 'struct dirent**')
    rewinddir = c.function_test('void', 'DIR*')
    seekdir = c.function_test('void', 'DIR*', 'long')
    telldir = c.function_test('long', 'DIR*')

# ------------------------------------------------------------------------------

class dlfcn_h(c.Header):
    RTLD_LAZY = c.macro_test()
    RTLD_NOW = c.macro_test()
    RTLD_GLOBAL = c.macro_test()
    RTLD_LOCAL = c.macro_test()
    dlclose = c.function_test('int', 'void*')
    dlerror = c.function_test('char*', 'void')
    dlopen = c.function_test('void*', 'const char*', 'int')
    dlsym = c.function_test('void*', 'void*', 'const char*')

# ------------------------------------------------------------------------------

class errno_h(c99.errno_h):
    E2BIG = c.variable_test()
    EACCES = c.variable_test()
    EADDRINUSE = c.variable_test()
    EADDRNOTAVAIL = c.variable_test()
    EAFNOSUPPORT = c.variable_test()
    EAGAIN = c.variable_test()
    EWOULDBLOCK = c.variable_test()
    EALREADY = c.variable_test()
    EBADF = c.variable_test()
    EBADMSG = c.variable_test()
    EBUSY = c.variable_test()
    ECANCELED = c.variable_test()
    ECHILD = c.variable_test()
    ECONNABORTED = c.variable_test()
    ECONNREFUSED = c.variable_test()
    ECONNRESET = c.variable_test()
    EDEADLK = c.variable_test()
    EDESTADDRREQ = c.variable_test()
    EDQUOT = c.variable_test()
    EEXIST = c.variable_test()
    EFAULT = c.variable_test()
    EFBIG = c.variable_test()
    EHOSTUNREACH = c.variable_test()
    EIDRM = c.variable_test()
    EINPROGRESS = c.variable_test()
    EINTR = c.variable_test()
    EINVAL = c.variable_test()
    EIO = c.variable_test()
    EISCONN = c.variable_test()
    EISDIR = c.variable_test()
    ELOOP = c.variable_test()
    EMFILE = c.variable_test()
    EMLINK = c.variable_test()
    EMSGSIZE = c.variable_test()
    EMULTIHOP = c.variable_test()
    ENAMETOOLONG = c.variable_test()
    ENETDOWN = c.variable_test()
    ENETRESET = c.variable_test()
    ENETUNREACH = c.variable_test()
    ENFILE = c.variable_test()
    ENOBUFS = c.variable_test()
    ENODATA = c.variable_test()
    ENODEV = c.variable_test()
    ENOENT = c.variable_test()
    ENOEXEC = c.variable_test()
    ENOLCK = c.variable_test()
    ENOLINK = c.variable_test()
    ENOMEM = c.variable_test()
    ENOMSG = c.variable_test()
    ENOPROTOOPT = c.variable_test()
    ENOSPC = c.variable_test()
    ENOSP = c.variable_test()
    ENOSTP = c.variable_test()
    ENOSYS = c.variable_test()
    ENOTCONN = c.variable_test()
    ENOTDIR = c.variable_test()
    ENOTEMPTY = c.variable_test()
    ENOTSOCK = c.variable_test()
    ENOTSUP = c.variable_test()
    ENOTTY = c.variable_test()
    ENXIO = c.variable_test()
    EOPNOTSUPP = c.variable_test()
    EOVERFLOW = c.variable_test()
    EPERM = c.variable_test()
    EPIPE = c.variable_test()
    EPROTO = c.variable_test()
    EPROTONOSUPPORT = c.variable_test()
    EPROTOTYPE = c.variable_test()
    EROFS = c.variable_test()
    ESPIPE = c.variable_test()
    ESRCH = c.variable_test()
    ESTALE = c.variable_test()
    ETIME = c.variable_test()
    ETIMEDOUT = c.variable_test()
    ETXTBSY = c.variable_test()
    EWOULDBLOCK = c.variable_test()
    EXDEV = c.variable_test()

# ------------------------------------------------------------------------------

class fcntl_h(c.Header):
    F_DUPFD = c.variable_test()
    F_GETFD = c.variable_test()
    F_SETFD = c.variable_test()
    F_GETFL = c.variable_test()
    F_SETFL = c.variable_test()
    F_GETLK = c.variable_test()
    F_SETLK = c.variable_test()
    F_SETLKW = c.variable_test()
    F_GETOWN = c.variable_test()
    F_SETOWN = c.variable_test()
    FD_CLOEXEC = c.variable_test()
    F_RDLCK = c.variable_test()
    F_UNLCK = c.variable_test()
    F_WRLCK = c.variable_test()
    O_CREAT = c.variable_test()
    O_EXCL = c.variable_test()
    O_NOCTTY = c.variable_test()
    O_TRUNC = c.variable_test()
    O_APPEND = c.variable_test()
    SIO = c.variable_test()
    O_NONBLOCK = c.variable_test()
    SIO = c.variable_test()
    O_SYNC = c.variable_test()
    O_ACCMODE = c.variable_test()
    O_RDONLY = c.variable_test()
    O_RDWR = c.variable_test()
    O_WRONLY = c.variable_test()
    mode_t = c.type_test()
    off_t = c.type_test()
    pid_t = c.type_test()
    POSIX_FADV_NORMAL = c.variable_test()
    POSIX_FADV_SEQUENTIAL = c.variable_test()
    POSIX_FADV_RANDOM = c.variable_test()
    POSIX_FADV_WILLNEED = c.variable_test()
    POSIX_FADV_DONTNEED = c.variable_test()
    POSIX_FADV_NOREUSE = c.variable_test()
    flock = c.struct_test(
        ('short', 'l_type'),
        ('short', 'l_whence'),
        ('off_t', 'l_start'),
        ('off_t', 'l_len'),
        ('pid_t', 'l_pid'))
    creat = c.function_test('int', 'const char*', 'mode_t')
    fcntl = c.function_test('int', 'int', 'int')
    open = c.function_test('int', 'const char*', 'int')
    posix_fadvise = c.function_test('int', 'int', 'off_t', 'off_t', 'int')
    posix_fallocate = c.function_test('int', 'int', 'off_t', 'off_t')

# ------------------------------------------------------------------------------

fenv_h = c99.fenv_h
float_h = c99.float_h

# ------------------------------------------------------------------------------

class fmtmsg_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class fnmatch_h(c.Header):
    pass

class ftw_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class glob_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class grp_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class iconv_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class inttypes_h(c99.inttypes_h):
    pass

# ------------------------------------------------------------------------------

iso646_h = c99.iso646_h

# ------------------------------------------------------------------------------

class langinfo_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class libgen_h(c.Header):
    pass

# ------------------------------------------------------------------------------

class limits_h(c99.limits_h):
    pass

# ------------------------------------------------------------------------------

class locale_h(c99.locale_h):
    pass

# ------------------------------------------------------------------------------

class math_h(c99.math_h):
    pass

class monetary_h(c.Header):
    pass

class mqueue_h(c.Header):
    pass

class ndbm_h(c.Header):
    pass

class netdb_h(c.Header):
    pass

class netinet_in_h(c.Header):
    pass

class netinet_tcp_h(c.Header):
    pass

class nl_types_h(c.Header):
    pass

class poll_h(c.Header):
    pass

class pthread_h(c.Header):
    PTHREAD_BARRIER_SERIAL_THREAD = c.macro_test()
    PTHREAD_CANCEL_ASYNCHRONOUS = c.macro_test()
    PTHREAD_CANCEL_ENABLE = c.macro_test()
    PTHREAD_CANCEL_DEFERRED = c.macro_test()
    PTHREAD_CANCEL_DISABLE = c.macro_test()
    PTHREAD_CANCELED = c.macro_test()
    PTHREAD_COND_INITIALIZER = c.macro_test()
    PTHREAD_CREATE_DETACHED = c.macro_test()
    PTHREAD_CREATE_JOINABLE = c.macro_test()
    PTHREAD_EXPLICIT_SCHED = c.macro_test()
    PTHREAD_INHERIT_SCHED = c.macro_test()
    PTHREAD_MUTEX_DEFAULT = c.macro_test()
    PTHREAD_MUTEX_ERRORCHECK = c.macro_test()
    PTHREAD_MUTEX_INITIALIZER = c.macro_test()
    PTHREAD_MUTEX_NORMAL = c.macro_test()
    PTHREAD_MUTEX_RECURSIVE = c.macro_test()
    PTHREAD_ONCE_INIT = c.macro_test()
    PTHREAD_PRIO_INHERIT = c.macro_test()
    PTHREAD_PRIO_NONE = c.macro_test()
    PTHREAD_PRIO_PROTECT = c.macro_test()
    PTHREAD_PROCESS_SHARED = c.macro_test()
    PTHREAD_PROCESS_PRIVATE = c.macro_test()
    PTHREAD_SCOPE_PROCESS = c.macro_test()
    PTHREAD_SCOPE_SYSTEM = c.macro_test()
    pthread_attr_t = c.type_test()
    pthread_barrier_t = c.type_test()
    pthread_barrierattr_t = c.type_test()
    pthread_cond_t = c.type_test()
    pthread_condattr_t = c.type_test()
    pthread_key_t = c.type_test()
    pthread_mutex_t = c.type_test()
    pthread_mutexattr_t = c.type_test()
    pthread_once_t = c.type_test()
    pthread_rwlock_t = c.type_test()
    pthread_rwlockattr_t = c.type_test()
    pthread_spinlock_t = c.type_test()
    pthread_t = c.type_test()
    pthread_atfork = c.function_test('int', 'void (*)(void)', 'void (*)(void)', 'void (*)(void)')
    pthread_attr_destroy = c.function_test('int', 'pthread_attr_t*')
    pthread_attr_getdetachstate = c.function_test('int', 'const pthread_attr_t*', 'int*')
    pthread_attr_getguardsize = c.function_test('int', 'const pthread_attr_t*', 'size_t*')
    pthread_attr_getinheritsched = c.function_test('int', 'const pthread_attr_t*', 'int*')
    pthread_attr_getschedparam = c.function_test('int', 'const pthread_attr_t*', 'struct sched_param*')
    pthread_attr_getschedpolicy = c.function_test('int', 'const pthread_attr_t*', 'int*')
    pthread_attr_getscope = c.function_test('int', 'const pthread_attr_t*', 'int*')
    pthread_attr_getstack = c.function_test('int', 'const pthread_attr_t*', 'void**', 'size_t*')
    pthread_attr_getstackaddr = c.function_test('int', 'const pthread_attr_t*', 'void**')
    pthread_attr_getstacksize = c.function_test('int', 'const pthread_attr_t*', 'size_t*')
    pthread_attr_init = c.function_test('int', 'pthread_attr_t*')
    pthread_attr_setdetachstate = c.function_test('int', 'pthread_attr_t*', 'int')
    pthread_attr_setguardsize = c.function_test('int', 'pthread_attr_t*', 'size_t')
    pthread_attr_setinheritsched = c.function_test('int', 'pthread_attr_t*', 'int')
    pthread_attr_setschedparam = c.function_test('int', 'pthread_attr_t*', 'const struct sched_param*')
    pthread_attr_setschedpolicy = c.function_test('int', 'pthread_attr_t*', 'int')
    pthread_attr_setscope = c.function_test('int', 'pthread_attr_t*', 'int')
    pthread_attr_setstack = c.function_test('int', 'pthread_attr_t*', 'void*', 'size_t')
    pthread_attr_setstackaddr = c.function_test('int', 'pthread_attr_t*', 'void*')
    pthread_attr_setstacksize = c.function_test('int', 'pthread_attr_t*', 'size_t')
    pthread_barrier_destroy = c.function_test('int', 'pthread_barrier_t*')
    pthread_barrier_init = c.function_test('int', 'pthread_barrier_t*', 'const pthread_barrierattr_t*', 'unsigned')
    pthread_barrier_wait = c.function_test('int', 'pthread_barrier_t*')
    pthread_barrierattr_destroy = c.function_test('int', 'pthread_barrierattr_t*')
    pthread_barrierattr_getpshared = c.function_test('int', 'const pthread_barrierattr_t*', 'int*')
    pthread_barrierattr_init = c.function_test('int', 'pthread_barrierattr_t*')
    pthread_barrierattr_setpshared = c.function_test('int', 'pthread_barrierattr_t*', 'int')
    pthread_cancel = c.function_test('int', 'pthread_t')
    pthread_cleanup_push = c.function_test('void', 'void (*)(void*)', 'void*')
    pthread_cleanup_pop = c.function_test('void', 'int')
    pthread_cond_broadcast = c.function_test('int', 'pthread_cond_t*')
    pthread_cond_destroy = c.function_test('int', 'pthread_cond_t*')
    pthread_cond_init = c.function_test('int', 'pthread_cond_t*', 'const pthread_condattr_t*')
    pthread_cond_signal = c.function_test('int', 'pthread_cond_t*')
    pthread_cond_timedwait = c.function_test('int', 'pthread_cond_t*', 'pthread_mutex_t*', 'const struct timespec*')
    pthread_cond_wait = c.function_test('int', 'pthread_cond_t*', 'pthread_mutex_t*')
    pthread_condattr_destroy = c.function_test('int', 'pthread_condattr_t*')
    pthread_condattr_getclock = c.function_test('int', 'const pthread_condattr_t*', 'clockid_t*')
    pthread_condattr_getpshared = c.function_test('int', 'const pthread_condattr_t*', 'int*')
    pthread_condattr_init = c.function_test('int', 'pthread_condattr_t*')
    pthread_condattr_setclock = c.function_test('int', 'pthread_condattr_t*', 'clockid_t')
    pthread_condattr_setpshared = c.function_test('int', 'pthread_condattr_t*', 'int')
    pthread_create = c.function_test('int', 'pthread_t*', 'const pthread_attr_t*', 'void* (*)(void*)', 'void*')
    pthread_detach = c.function_test('int', 'pthread_t')
    pthread_equal = c.function_test('int', 'pthread_t', 'pthread_t')
    pthread_exit = c.function_test('void', 'void*')
    pthread_getconcurrency = c.function_test('int', 'void')
    pthread_getcpuclockid = c.function_test('int', 'pthread_t', 'clockid_t*')
    pthread_getschedparam = c.function_test('int', 'pthread_t', 'int*', 'struct sched_param*')
    pthread_getspecific = c.function_test('void*', 'pthread_key_t')
    pthread_join = c.function_test('int', 'pthread_t', 'void**')
    pthread_key_create = c.function_test('int', 'pthread_key_t*', 'void (*)(void*)')
    pthread_key_delete = c.function_test('int', 'pthread_key_t')
    pthread_mutex_destroy = c.function_test('int', 'pthread_mutex_t*')
    pthread_mutex_getprioceiling = c.function_test('int', 'const pthread_mutex_t*', 'int*')
    pthread_mutex_init = c.function_test('int', 'pthread_mutex_t*', 'const pthread_mutexattr_t*')
    pthread_mutex_lock = c.function_test('int', 'pthread_mutex_t*')
    pthread_mutex_setprioceiling = c.function_test('int', 'pthread_mutex_t*', 'int', 'int*')
    pthread_mutex_timedlock = c.function_test('int', 'pthread_mutex_t*', 'const struct timespec*')
    pthread_mutex_trylock = c.function_test('int', 'pthread_mutex_t*')
    pthread_mutex_unlock = c.function_test('int', 'pthread_mutex_t*')
    pthread_mutexattr_destroy = c.function_test('int', 'pthread_mutexattr_t*')
    pthread_mutexattr_getprioceiling = c.function_test('int', 'const pthread_mutexattr_t*', 'int*')
    pthread_mutexattr_getprotocol = c.function_test('int', 'const pthread_mutexattr_t*', 'int*')
    pthread_mutexattr_getpshared = c.function_test('int', 'const pthread_mutexattr_t*', 'int*')
    pthread_mutexattr_gettype = c.function_test('int', 'const pthread_mutexattr_t*', 'int*')
    pthread_mutexattr_init = c.function_test('int', 'pthread_mutexattr_t*')
    pthread_mutexattr_setprioceiling = c.function_test('int', 'pthread_mutexattr_t*', 'int')
    pthread_mutexattr_setprotocol = c.function_test('int', 'pthread_mutexattr_t*', 'int')
    pthread_mutexattr_setpshared = c.function_test('int', 'pthread_mutexattr_t*', 'int')
    pthread_mutexattr_settype = c.function_test('int', 'pthread_mutexattr_t*', 'int')
    pthread_once = c.function_test('int', 'pthread_once_t*', 'void (*)(void)')
    pthread_rwlock_destroy = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlock_init = c.function_test('int', 'pthread_rwlock_t*', 'const pthread_rwlockattr_t*')
    pthread_rwlock_rdlock = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlock_timedrdlock = c.function_test('int', 'pthread_rwlock_t*', 'const struct timespec*')
    pthread_rwlock_timedwrlock = c.function_test('int', 'pthread_rwlock_t*', 'const struct timespec*')
    pthread_rwlock_tryrdlock = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlock_trywrlock = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlock_unlock = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlock_wrlock = c.function_test('int', 'pthread_rwlock_t*')
    pthread_rwlockattr_destroy = c.function_test('int', 'pthread_rwlockattr_t*')
    pthread_rwlockattr_getpshared = c.function_test('int', 'const pthread_rwlockattr_t*', 'int*')
    pthread_rwlockattr_init = c.function_test('int', 'pthread_rwlockattr_t*')
    pthread_rwlockattr_setpshared = c.function_test('int', 'pthread_rwlockattr_t*', 'int')
    pthread_self = c.function_test('pthread_t', 'void')
    pthread_setcancelstate = c.function_test('int', 'int', 'int*')
    pthread_setcanceltype = c.function_test('int', 'int', 'int*')
    pthread_setconcurrency = c.function_test('int', 'int')
    pthread_setschedparam = c.function_test('int', 'pthread_t', 'int', 'const struct sched_param*')
    pthread_setschedprio = c.function_test('int', 'pthread_t', 'int')
    pthread_setspecific = c.function_test('int', 'pthread_key_t', 'const void*')
    pthread_spin_destroy = c.function_test('int', 'pthread_spinlock_t*')
    pthread_spin_init = c.function_test('int', 'pthread_spinlock_t*', 'int')
    pthread_spin_lock = c.function_test('int', 'pthread_spinlock_t*')
    pthread_spin_trylock = c.function_test('int', 'pthread_spinlock_t*')
    pthread_spin_unlock = c.function_test('int', 'pthread_spinlock_t*')
    pthread_testcancel = c.function_test('void', 'void')



class pwd_h(c.Header):
    pass

class regex_h(c.Header):
    pass

class sched_h(c.Header):
    pass

class search_h(c.Header):
    pass

class semaphore_h(c.Header):
    pass

class setjmp_h(c99.setjmp_h):
    pass

class signal_h(c99.signal_h):
    pass

class spawn_h(c.Header):
    pass

class stdarg_h(c99.stdarg_h):
    pass

stdbool_h = c99.stdbool_h
stddef_h = c99.stddef_h

class stdint_h(c99.stdint_h):
    pass

class stdio_h(c99.stdio_h):
    pass

class stdlib_h(c99.stdlib_h):
    pass

class string_h(c99.string_h):
    pass

class strings_h(c.Header):
    pass

class stropts_h(c.Header):
    pass

class sys_ipc_h(c.Header):
    header = 'sys/ipc.h'

class sys_mman_h(c.Header):
    header = 'sys/mman.h'

    MAP_FAILED = c.macro_test()
    MAP_FIXED = c.macro_test()
    MAP_PRIVATE = c.macro_test()
    MAP_SHARED = c.macro_test()
    MCL_CURRENT = c.macro_test()
    MCL_FUTURE = c.macro_test()
    MS_ASYNC = c.macro_test()
    MS_INVALIDATE = c.macro_test()
    MS_SYNC = c.macro_test()
    POSIX_MADV_DONTNEED = c.macro_test()
    POSIX_MADV_NORMAL = c.macro_test()
    POSIX_MADV_RANDOM = c.macro_test()
    POSIX_MADV_SEQUENTIAL = c.macro_test()
    POSIX_MADV_WILLNEED = c.macro_test()
    POSIX_TYPED_MEM_ALLOCATE = c.macro_test()
    POSIX_TYPED_MEM_ALLOCATE_CONTIG = c.macro_test()
    POSIX_TYPED_MEM_MAP_ALLOCATABLE = c.macro_test()
    PROT_EXEC = c.macro_test()
    PROT_NONE = c.macro_test()
    PROT_READ = c.macro_test()
    PROT_WRITE = c.macro_test()
    mode_t = c.type_test()
    off_t = c.type_test()
    size_t = c.type_test()
    posix_typed_mem_info = c.struct_test(
        ('size_t', 'posix_tmi_length'))
    mlock = c.function_test('int', 'const void*', 'size_t')
    mlockall = c.function_test('int', 'int')
    mmap = c.function_test('void*', 'size_t', 'int', 'int', 'int', 'off_t')
    mprotect = c.function_test('int', 'void*', 'size_t', 'int')
    msync = c.function_test('int', 'void*', 'size_t', 'int')
    munlock = c.function_test('int', 'const void*', 'size_t')
    munlockall = c.function_test('int', 'void')
    munmap = c.function_test('int', 'void*', 'size_t')
    posix_madvise = c.function_test('int', 'void*', 'size_t', 'int')
    posix_mem_offset = c.function_test('int', 'const void*', 'size_t', 'off_t*', 'size_t*', 'int*')
    posix_typed_mem_get_info = c.function_test('int', 'int', 'struct posix_typed_mem_info*')
    posix_typed_mem_open = c.function_test('int', 'const char*', 'int', 'int')
    shm_open = c.function_test('int', 'const char*', 'int', 'mode_t')
    shm_unlink = c.function_test('int', 'const char*')

class sys_msg_h(c.Header):
    header = 'sys/msg.h'

class sys_resource_h(c.Header):
    header = 'sys/resource.h'

class sys_select_h(c.Header):
    header = 'sys/select.h'

class sys_sem_h(c.Header):
    header = 'sys/sem.h'

class sys_shm_h(c.Header):
    header = 'sys/shm.h'

class sys_socket_h(c.Header):
    header = 'sys/socket.h'

class sys_stat_h(c.Header):
    header = 'sys/stat.h'

class sys_statvfs_h(c.Header):
    header = 'sys/statvfs.h'

class sys_time_h(c.Header):
    header = 'sys/time.h'

class sys_timeb_h(c.Header):
    header = 'sys/timeb.h'

class sys_times_h(c.Header):
    header = 'sys/times.h'

class sys_types_h(c.Header):
    header = 'sys/types.h'

class sys_uio_h(c.Header):
    header = 'sys/uio.h'

class sys_un_h(c.Header):
    header = 'sys/un.h'

class sys_utsname_h(c.Header):
    header = 'sys/utsname.h'

class sys_wait_h(c.Header):
    header = 'sys/wait.h'

class syslog_h(c.Header):
    pass

class tar_h(c.Header):
    pass

class termios_h(c.Header):
    pass

tgmath_h = c99.tgmath_h

class time_h(c99.time_h):
    pass

class trace_h(c.Header):
    pass

class ucontext_h(c.Header):
    pass

class ulimit_h(c.Header):
    pass

class unistd_h(c.Header):
    pass

class utime_h(c.Header):
    pass

class utmpx_h(c.Header):
    pass

class wchar_h(c99.wchar_h):
    pass

class wctype_h(c99.wctype_h):
    pass

class wordexp_h(c.Header):
    pass
    pass
