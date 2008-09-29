from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# -----------------------------------------------------------------------------

def config_sys_epoll_h(env, builder):
    if not builder.check_header_exists('sys/epoll.h'):
        raise MissingHeader('sys/epoll.h')

    epoll = builder.check_run('''
        #include <sys/epoll.h>

        int main(int argc, char** argv) {
            int efd = epoll_create(20);
            return (-1 == efd) ? 1 : 0;
        }
    ''', 'checking if epoll is supported')

    return Record(epoll=epoll)

# -----------------------------------------------------------------------------

def config_headers(env, builder):
    return Record(
        sys=Record(
            epoll_h=env.config(config_sys_epoll_h, builder),
        ),
    )

def config(env, builder):
    return Record(
        headers=env.config(config_headers, builder),
    )
