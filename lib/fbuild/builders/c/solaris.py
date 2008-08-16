from . import MissingHeader

# -----------------------------------------------------------------------------

def config_port_h(env):
    if not env['static'].check_header_exists('port.h'):
        raise MissingHeader('port.h')

    port_h = env.setdefault('headers', {}).setdefault('port_h', {})
    port_h['port_create'] = env['static'].check_run('''
        #include <port.h>
        int main(int argc, char** argv) {
            int port = port_create();
            if (port < 0) { return 1; }
            if (close(port) < 0) { return 1; }
            return 0;
        }
    ''', 'checking if evtports is supported')

def config(env):
    config_port_h(env)
