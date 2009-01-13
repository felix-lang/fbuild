import fbuild.builders.c
import fbuild.db
from fbuild import ConfigFailed, logger
from fbuild.record import Record
from fbuild.builders.c import std, MissingHeader

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_dlfcn_h(builder, shared=None):
    '''
    Test for the posix dlfcn.h header, which provides for dynamically loading
    libraries.

    @param builder: C builder
    @param shared: C builder that can create dynamically loadable libraries.
                   If none is provided, try to configure a standard c shared
                   builder.
    '''

    if not builder.check_header_exists('dlfcn.h'):
        raise MissingHeader('dlfcn.h')

    if shared is None:
        shared = fbuild.builders.c.guess_shared()

    lib_code = '''
        #ifdef __cplusplus
        extern "C" {
        #endif
        int fred(int argc, char** argv) { return 0; }
        #ifdef __cplusplus
        }
        #endif
    '''

    exe_code = '''
        #include <dlfcn.h>
        #include <stdlib.h>

        int main(int argc, char** argv) {
            void* lib = dlopen("%s", RTLD_NOW);
            void* fred = 0;
            if(!lib) exit(1);
            fred = dlsym(lib,"fred");
            if(!fred) exit(1);
            return 0;
        }
    '''

    with builder.tempfile(lib_code) as lib_src:
        obj = shared.compile(lib_src, quieter=1)
        lib = shared.link_lib(lib_src.parent / 'temp', [obj], quieter=1)

        dlopen = builder.check_run(exe_code % lib,
            'check if supports dlopen')

    return Record(dlopen=dlopen)

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_sys_mman_h(builder):
    '''
    Test for the posix sys/mman.h header, which provides memory mapped files.

    @param builder: C builder
    '''

    if not builder.check_header_exists('sys/mman.h'):
        raise MissingHeader('sys/mman.h')

    mman_h = Record()
    mman_h.macros = {}

    for macro in (
            'PROT_EXEC', 'PROT_READ', 'PROT_WRITE', 'MAP_DENYWRITE',
            'MAP_ANON', 'MAP_FILE', 'MAP_FIXED', 'MAP_HASSEMAPHORE',
            'MAP_SHARED', 'MAP_PRIVATE', 'MAP_NORESERVE', 'MAP_LOCKED',
            'MAP_GROWSDOWN', 'MAP_32BIT', 'MAP_POPULATE', 'MAP_NONBLOCK'):
        mman_h.macros[macro] = builder.check_macros_exist(macro,
            headers=['sys/mman.h'])

    return mman_h

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_poll_h(builder):
    '''
    Test for the posix poll.h header, which provides asynchronous io.

    @param builder: C builder
    '''

    if not builder.check_header_exists('poll.h'):
        raise MissingHeader('poll.h')

    # just check if the header exists for now
    return Record()

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_pthread_h(builder):
    '''
    Test for the posix pthread.h header, which provides posix threads.

    @param builder: C builder
    '''

    if not builder.check_header_exists('pthread.h'):
        raise MissingHeader('pthread.h')

    pthread_h = Record()

    code = '''
        #include <pthread.h>

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

    logger.check('detecting pthread link flags')
    for flags in [], ['-lpthread'], ['-pthread'], ['-pthreads']:
        if builder.try_run(code, lkwargs={'flags': flags}):
            logger.passed('ok %r' % ' '.join(flags))
            pthread_h.flags = flags
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to link pthread program')

    return pthread_h

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_sys_socket_h(builder):
    '''
    Test for the posix sys/socket.h header, which provides network sockets.

    @param builder: C builder
    '''

    if not builder.check_header_exists('sys/socket.h'):
        raise MissingHeader('sys/socket.h')

    socket_h = Record()

    code = '''
        #include <sys/types.h>
        #include <sys/socket.h>

        extern int accept(int s, struct sockaddr* addr, %s* addrlen);
    '''

    logger.check('determing type of socklen_t')
    for t in 'socklen_t', 'unsigned int', 'int':
        if builder.try_compile(code % t):
            logger.passed('ok ' + t)
            socket_h.socklen_t = t
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to detect type of socklen_t')

    return socket_h

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

@fbuild.db.caches
def config_unistd_h(builder):
    '''
    Test for the posix unistd.h header, which provides standard posix types.

    @param builder: C builder
    '''

    if not builder.check_header_exists('unistd.h'):
        raise MissingHeader('unistd.h')

    return Record(
        types=std.get_types_data(builder, default_types_unistd_h,
            headers=['unistd.h']),
    )

# -----------------------------------------------------------------------------

def config_headers(builder, shared=None):
    '''
    Test if the builder supports the posix headers.

    @param builder: C builder
    @param shared: C builder that can create dynamically loadable libraries
    '''

    return Record(
        dlfcn_h=config_dlfcn_h(builder, shared),
        poll_h=config_poll_h(builder),
        pthread_h=config_pthread_h(builder),
        unistd_h=config_unistd_h(builder),
        sys=Record(
            mman_h=config_sys_mman_h(builder),
            socket_h=config_sys_socket_h(builder),
        ),
    )

def config(builder, shared=None):
    '''
    Test if the builder is posix-compatible.

    @param builder: C builder
    @param shared: C builder that can create dynamically loadable libraries
    '''

    return Record(
        headers=config_headers(builder, shared),
    )

# -----------------------------------------------------------------------------

def types_unistd_h():
    return (t for t in default_types_unistd_h if t in env.posix.unistd.types)
