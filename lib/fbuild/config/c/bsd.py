import fbuild.config.c as c

# ------------------------------------------------------------------------------

class sys_event_h(c.Header):
    header = 'sys/event.h'

    kqueue = c.function_test('int', 'void', test='''
        #include <sys/types.h>      // from the kqueue manpage
        #include <sys/event.h>      // kernel events
        #include <sys/time.h>       // timespec (kevent timeout)

        int main(int argc, char** argv) {
            int kq = kqueue();
            return (-1 == kq) ? 1 : 0;
        }
        ''')
