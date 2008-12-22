import fbuild.db
from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_windows_h(builder):
    if not builder.check_header_exists('windows.h'):
        raise MissingHeader('windows.h')

    LoadLibrary = builder.check_compile('''
        #include <windows.h>
        #include <stdlib.h>

        int main(int argc,char** argv) {
            HMODULE lib = LoadLibrary(argv[1]);
            void *fred;
            if(!lib) return 1;
            fred = (void*)GetProcAddress(lib,"fred");
            if(!fred) return 1;
            return 0;
        }
    ''', 'checking if supports LoadLibrary')

    return Record(LoadLibrary=LoadLibrary)

def config_headers(builder):
    return Record(
        windows_h=config_windows_h(builder),
    )

def config(builder):
    return Record(
        headers=config_headers(builder),
    )
