from fbuild import ConfigFailed
from . import std

# -----------------------------------------------------------------------------

default_types_unistd_h = (
    'pid_t',
    'gid_t',
    'intptr_t',
    'off_t',
    'size_t',
    'ssize_t',
    'uid_t',
    'useconds_t',
    'uuid_t',
)

# -----------------------------------------------------------------------------

def detect_mmap_macros(builder):
    return {m: builder.check_macro_exists(m, headers=['sys/mman.h'])
        for m in (
            'PROT_EXEC', 'PROT_READ', 'PROT_WRITE', 'MAP_DENYWRITE',
            'MAP_ANON', 'MAP_FILE', 'MAP_FIXED', 'MAP_HASSEMAPHORE',
            'MAP_SHARED', 'MAP_PRIVATE', 'MAP_NORESERVE', 'MAP_LOCKED',
            'MAP_GROWSDOWN', 'MAP_32BIT', 'MAP_POPULATE', 'MAP_NONBLOCK',
        )
    }

# -----------------------------------------------------------------------------

def detect_pthread_flags(builder):
    code = '''
        void* start(void* data) { return NULL; }

        int main(int argc, char** argv) {
            pthread_t thr;
            pthread_attr_t attr;
            pthread_attr_init(&attr);
            pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
            int res = pthread_create(&thr, &attr, start, NULL);
            pthread_attr_destroy(&attr);
            return res;
        }
    '''

    builder.check('detecting pthread link flags')
    for flags in [], ['-lpthread'], ['-pthread'], ['-pthreads']:
        if builder.try_run(code,
                headers=['pthread.h'],
                lflags={'flags': flags}):
            builder.log('ok %r' % ' '.join(flags), color='green')
            return flags
    else:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to link pthread program')

# -----------------------------------------------------------------------------

def detect_socklen_t(builder):
    code = 'extern int accept(int s, struct sockaddr* addr, %s* addrlen);'

    builder.check('determing type of socklen_t')
    for t in 'socklen_t', 'unsigned int', 'int':
        if builder.try_compile(code % t,
                headers=['sys/types.h', 'sys/socket.h']):
            builder.log('ok ' + t, color='green')
            return t
    else:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to detect type of socklen_t')

# -----------------------------------------------------------------------------

def config_pthread_h(conf, builder):
    if not builder.check_header_exists('pthread.h'):
        raise ConfigFailed('missing pthread.h')

    conf.configure('pthread_h.flags', detect_pthread_flags, builder)

def config_sys_mman_h(conf, builder):
    if not builder.check_header_exists('sys/mman.h'):
        raise ConfigFailed('missing sys/mman.h')

    conf.configure('sys.mman_h.macros', detect_mmap_macros, builder)

def config_sys_socket_h(conf, builder):
    if not builder.check_header_exists('sys/socket.h'):
        raise ConfigFailed('missing sys/socket.h')

    conf.configure('sys.socket_h.socklen_t', detect_socklen_t, builder)

def config_unistd_h(conf, builder):
    if not builder.check_header_exists('unistd.h'):
        raise ConfigFailed('missing unistd.h')

    conf.configure('unistd_h.types',
        std.get_types_data, builder, default_types_unistd_h,
        headers=['unistd.h'])

def config(conf, builder):
    config_pthread_h(conf, builder)
    config_sys_mman_h(conf, builder)
    config_sys_socket_h(conf, builder)
    config_unistd_h(conf, builder)

# -----------------------------------------------------------------------------

def types_unistd_h(conf):
    return (t for t in default_types_unistd_h if t in conf.posix.unistd.types)
