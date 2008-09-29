from fbuild.record import Record
from fbuild.builders.c import MissingHeader

# -----------------------------------------------------------------------------

def config_sys_event_h(env, builder):
    if not builder.check_header_exists('sys/event.h'):
        raise MissingHeader('sys/event.h')

    kqueue = builder.check_run('''
        #include <sys/types.h>      // from the kqueue manpage
        #include <sys/event.h>      // kernel events
        #include <sys/time.h>       // timespec (kevent timeout)

        int main(int argc, char** argv) {
            int kq = kqueue();
            return (-1 == kq) ? 1 : 0;
        }
    ''', 'checking if kqueue is supported')

    return Record(kqueue=kqueue)

# -----------------------------------------------------------------------------

def config_headers(env, builder):
    return Record(
        sys=Record(
            event_h=env.config(config_sys_event_h, builder),
        ),
    )

def config(env, builder):
    return Record(
        headers=env.config(config_headers, builder),
    )
