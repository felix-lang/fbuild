import os

from fbuild import ConfigFailed
from . import std, MissingHeader

# -----------------------------------------------------------------------------

def config_dlfcn_h(conf):
    if not conf.static.check_header_exists('dlfcn.h'):
        raise MissingHeader('dlfcn.h')

    dlfcn_h = conf.config_group('headers.dlfcn_h')

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

    with conf.shared.tempfile(lib_code) as lib_src:
        obj = conf.shared.compile([lib_src], quieter=1)
        lib = conf.shared.link_lib((os.path.dirname(lib_src), 'temp'), obj,
            quieter=1)

        dlfcn_h.dlopen = conf.static.check_run(exe_code % lib,
            'check if supports dlopen')

# -----------------------------------------------------------------------------

def config_sys_mman_h(conf):
    if not conf.static.check_header_exists('sys/mman.h'):
        raise MissingHeader('sys/mman.h')

    mman_h = conf.config_group('headers.sys.mman_h')
    mman_h.macros = {m: conf.static.check_macro_exists(m,
            headers=['sys/mman.h'])
        for m in (
            'PROT_EXEC', 'PROT_READ', 'PROT_WRITE', 'MAP_DENYWRITE',
            'MAP_ANON', 'MAP_FILE', 'MAP_FIXED', 'MAP_HASSEMAPHORE',
            'MAP_SHARED', 'MAP_PRIVATE', 'MAP_NORESERVE', 'MAP_LOCKED',
            'MAP_GROWSDOWN', 'MAP_32BIT', 'MAP_POPULATE', 'MAP_NONBLOCK',
        )
    }

# -----------------------------------------------------------------------------

def config_pthread_h(conf):
    if not conf.static.check_header_exists('pthread.h'):
        raise MissingHeader('pthread.h')

    pthread_h = conf.config_group('headers.pthread_h')

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

    conf.check('detecting pthread link flags')
    for flags in [], ['-lpthread'], ['-pthread'], ['-pthreads']:
        if conf.static.try_run(code,
                headers=['pthread.h'],
                lflags={'flags': flags}):
            conf.log('ok %r' % ' '.join(flags), color='green')
            pthread_h.flags = flags
            break
    else:
        conf.log('failed', color='yellow')
        raise ConfigFailed('failed to link pthread program')

# -----------------------------------------------------------------------------

def config_sys_socket_h(conf):
    if not conf.static.check_header_exists('sys/socket.h'):
        raise MissingHeader('sys/socket.h')

    socket_h = conf.config_group('headers.sys.socket_h')

    code = 'extern int accept(int s, struct sockaddr* addr, %s* addrlen);'

    conf.check('determing type of socklen_t')
    for t in 'socklen_t', 'unsigned int', 'int':
        if conf.static.try_compile(code % t,
                headers=['sys/types.h', 'sys/socket.h']):
            conf.log('ok ' + t, color='green')
            socket_h.socklen_t = t
            break
    else:
        conf.log('failed', color='yellow')
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
    if not conf.static.check_header_exists('unistd.h'):
        raise MissingHeader('unistd.h')

    unistd_h = conf.config_group('headers.unistd_h')
    unistd_h.types = std.get_types_data(conf.static, default_types_unistd_h,
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
