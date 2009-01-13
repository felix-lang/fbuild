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
        ('char*', 'd_name'),
        name='struct dirent')
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
    pass

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
