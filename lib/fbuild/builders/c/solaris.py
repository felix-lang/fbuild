import fbuild.db
from fbuild.record import Record
from fbuild.builders.c import MissingHeader

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_port_h(builder):
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

def config_headers(builder):
    return Record(
        port_h=config_port_h(builder),
    )

def config(builder):
    return Record(
        headers=config_headers(builder),
    )
