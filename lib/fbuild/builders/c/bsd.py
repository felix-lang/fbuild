from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_sys_event_h(conf, builder):
    if not builder.check_header_exists('sys/event.h'):
        raise ConfigFailed('missing sys/event.h')

    conf.configure('sys.event_h', builder.check_run, '''
        #include <sys/types.h>      // from the kqueue manpage
        #include <sys/event.h>      // kernel events
        #include <sys/time.h>       // timespec (kevent timeout)

        int main(int argc, char** argv) {
            int kq = kqueue();
            return (-1 == kq) ? 1 : 0;
        }
    ''', 'checking if kqueue is supported')

def config(conf, builder):
    config_sys_event_h(conf, builder)
