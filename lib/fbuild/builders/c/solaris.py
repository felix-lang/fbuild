from fbuild import Record
from . import MissingHeader

# -----------------------------------------------------------------------------

def config_port_h(env, builder):
    if not builder.check_header_exists('port.h'):
        raise MissingHeader('port.h')

    port_create = builder.check_run('''
        #include <port.h>
        int main(int argc, char** argv) {
            int port = port_create();
            if (port < 0) { return 1; }
            if (close(port) < 0) { return 1; }
            return 0;
        }
    ''', 'checking if evtports is supported')

    return Record(port_create=port_create)

# -----------------------------------------------------------------------------

def config_headers(env, builder):
    return Record(
        port_h=env.config(config_port_h, builder),
    )

def config(env, builder):
    return Record(
        headers=env.config(config_headers, builder),
    )
