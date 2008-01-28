from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_port_h(conf, builder):
    if not builder.check_header_exists('port.h'):
        raise ConfigFailed('missing port.h')

    conf.configure('port_h', builder.check_run, '''
        #include <port.h>
        int main(int argc, char** argv) {
            int port = port_create();
            if (port < 0) { return 1; }
            if (close(port) < 0) { return 1; }
            return 0;
        }
    ''', 'checking if evtports is supported')

def config(conf, builder):
    config_port_h(conf, builder)
