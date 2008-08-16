from . import MissingHeader

# -----------------------------------------------------------------------------

def config_sys_event_h(env, builder):
    if not builder.check_header_exists('sys/event.h'):
        raise MissingHeader('sys/event.h')

    event_h = env.setdefault('headers', {}) \
                  .setdefault('sys', {}) \
                  .setdefault('event_h', {})
    event_h['kqueue'] = builder.check_run('''
        #include <sys/types.h>      // from the kqueue manpage
        #include <sys/event.h>      // kernel events
        #include <sys/time.h>       // timespec (kevent timeout)

        int main(int argc, char** argv) {
            int kq = kqueue();
            return (-1 == kq) ? 1 : 0;
        }
    ''', 'checking if kqueue is supported')

def config(env, builder):
    config_sys_event_h(env, builder)
