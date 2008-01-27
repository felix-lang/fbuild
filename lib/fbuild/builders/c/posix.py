from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def detect_mmap(builder):
    if not builder.check_header_exists('sys/mman.h'):
        raise ConfigFailed('missing sys/mman.h')

    macros = {m: builder.check_macro_exists(m, headers=['sys/mman.h'])
        for m in (
            'PROT_EXEC', 'PROT_READ', 'PROT_WRITE', 'MAP_DENYWRITE', 'MAP_ANON',
            'MAP_FILE', 'MAP_FIXED', 'MAP_HASSEMAPHORE', 'MAP_SHARED',
            'MAP_PRIVATE', 'MAP_NORESERVE', 'MAP_LOCKED', 'MAP_GROWSDOWN',
            'MAP_32BIT', 'MAP_POPULATE', 'MAP_NONBLOCK',
        )
    }

    return {'macros': macros}

# -----------------------------------------------------------------------------

def detect_pthread(builder):
    if not builder.check_header_exists('pthread.h'):
        raise ConfigFailed('missing pthread.h')

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
            break
    else:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to link pthread program')

    return {'flags': flags}

# -----------------------------------------------------------------------------

def detect_socket(builder):
    if not builder.check_header_exists('sys/socket.h'):
        raise ConfigFailed('missing sys/socket.h')

    code = 'extern int accept(int s, struct sockaddr* addr, %s* addrlen);'

    builder.check('determing type of socklen_t')
    for t in 'socklen_t', 'unsigned int', 'int':
        if builder.try_compile(code %t,
                headers=['sys/types.h', 'sys/socket.h']):
            builder.log('ok ' + t, color='green')
            break
    else:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to detect type of socklen_t')

    return {'socklen_t': t}

# -----------------------------------------------------------------------------

def config_mmap(conf, builder):
    conf.configure('mmap', detect_mmap, builder)

def config_pthreads(conf, builder):
    conf.configure('pthread.flags', detect_pthread, builder)

def config_sockets(conf, builder):
    conf.configure('posix.socklen_t', detect_socket, builder)

def config(conf, builder):
    conf.subconfigure('posix', config_mmap, builder)
    conf.subconfigure('posix', config_pthreads, builder)
    conf.subconfigure('posix', config_sockets, builder)
