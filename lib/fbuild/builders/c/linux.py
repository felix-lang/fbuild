from . import MissingHeader

# -----------------------------------------------------------------------------

def config_sys_epoll_h(conf):
    if not conf.static.check_header_exists('sys/epoll.h'):
        raise MissingHeader('sys/epoll.h')

    epoll_h = conf.config_group('headers.sys.epoll_h')
    epoll_h.epoll = conf.static.check_run('''
        #include <sys/epoll.h>

        int main(int argc, char** argv) {
            int efd = epoll_create(20);
            return (-1 == efd) ? 1 : 0;
        }
    ''', 'checking if epoll is supported')

def config(conf):
    config_sys_epoll_h(conf)
