import os

from fbuild import logger, ConfigFailed
from fbuild.temp import tempfile
from . import std, MissingHeader

# -----------------------------------------------------------------------------

def config_dlfcn_h(conf):
    static = conf['static']
    shared = conf['shared']

    if not static.check_header_exists('dlfcn.h'):
        raise MissingHeader('dlfcn.h')

    dlfcn_h = conf.setdefault('headers', {}).setdefault('dlfcn_h', {})

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

    with tempfile(lib_code, shared.src_suffix) as lib_src:
        obj = shared.compile(lib_src, quieter=1)
        lib = shared.link_lib((os.path.dirname(lib_src), 'temp'), [obj],
            quieter=1)

        dlfcn_h['dlopen'] = static.check_run(exe_code % lib,
            'check if supports dlopen')

# -----------------------------------------------------------------------------

def config_sys_mman_h(conf):
    static = conf['static']
    if not static.check_header_exists('sys/mman.h'):
        raise MissingHeader('sys/mman.h')

    mman_h = conf.setdefault('headers', {}) \
                 .setdefault('sys', {}) \
                 .setdefault('mman_h', {})
    mman_h['macros'] = {m: static.check_macro_exists(m, headers=['sys/mman.h'])
        for m in (
            'PROT_EXEC', 'PROT_READ', 'PROT_WRITE', 'MAP_DENYWRITE',
            'MAP_ANON', 'MAP_FILE', 'MAP_FIXED', 'MAP_HASSEMAPHORE',
            'MAP_SHARED', 'MAP_PRIVATE', 'MAP_NORESERVE', 'MAP_LOCKED',
            'MAP_GROWSDOWN', 'MAP_32BIT', 'MAP_POPULATE', 'MAP_NONBLOCK',
        )
    }

# -----------------------------------------------------------------------------

def config_pthread_h(conf):
    static = conf['static']
    if not static.check_header_exists('pthread.h'):
        raise MissingHeader('pthread.h')

    pthread_h = conf.setdefault('headers', {}).setdefault('pthread_h', {})

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
        if static.try_run(code,
                lflags={'flags': flags}):
            logger.passed('ok %r' % ' '.join(flags))
            pthread_h['flags'] = flags
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to link pthread program')

# -----------------------------------------------------------------------------

def config_sys_socket_h(conf):
    static = conf['static']
    if not static.check_header_exists('sys/socket.h'):
        raise MissingHeader('sys/socket.h')

    socket_h = conf.setdefault('headers', {}) \
                   .setdefault('sys', {}) \
                   .setdefault('socket_h', {})

    code = '''
        #include <sys/types.h>
        #include <sys/socket.h>

        extern int accept(int s, struct sockaddr* addr, %s* addrlen);
    '''

    logger.check('determing type of socklen_t')
    for t in 'socklen_t', 'unsigned int', 'int':
        if static.try_compile(code % t):
            logger.passed('ok ' + t)
            socket_h['socklen_t'] = t
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to detect type of socklen_t')

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

def config_unistd_h(conf):
    static = conf['static']
    if not static.check_header_exists('unistd.h'):
        raise MissingHeader('unistd.h')

    unistd_h = conf.setdefault('headers', {}).setdefault('unistd_h', {})
    unistd_h['types'] = std.get_types_data(static, default_types_unistd_h,
        headers=['unistd.h'])

# -----------------------------------------------------------------------------

def config(conf):
    config_dlfcn_h(conf)
    config_pthread_h(conf)
    config_sys_mman_h(conf)
    config_sys_socket_h(conf)
    config_unistd_h(conf)

# -----------------------------------------------------------------------------

def types_unistd_h(conf):
    return (t for t in default_types_unistd_h if t in conf.posix.unistd.types)
