from . import MissingHeader

# -----------------------------------------------------------------------------

def config_sys_epoll_h(env, builder):
    if not builder.check_header_exists('sys/epoll.h'):
        raise MissingHeader('sys/epoll.h')

    epoll_h = env.setdefault('headers', {}) \
                  .setdefault('sys', {}) \
                  .setdefault('epoll_h', {})
    epoll_h['epoll'] = builder.check_run('''
        #include <sys/epoll.h>

        int main(int argc, char** argv) {
            int efd = epoll_create(20);
            return (-1 == efd) ? 1 : 0;
        }
    ''', 'checking if epoll is supported')

def config(env, builder):
    config_sys_epoll_h(env, builder)
