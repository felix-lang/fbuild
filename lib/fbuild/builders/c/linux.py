from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_sys_epoll_h(conf):
    if not conf.static.check_header_exists('sys/epoll.h'):
        raise ConfigFailed('missing sys/epoll.h')

    conf.configure('sys.epoll_h', conf.static.check_run, '''
        #include <sys/epoll.h>

        int main(int argc, char** argv) {
            int efd = epoll_create(20);
            return (-1 == efd) ? 1 : 0;
        }
    ''', 'checking if epoll is supported')

def config(conf):
    config_sys_epoll_h(conf)
