from fbuild import Record
from . import MissingHeader

# -----------------------------------------------------------------------------

def config_windows_h(env, builder):
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

def config_headers(env, builder):
    return Record(
        windows_h=env.config(config_windows_h, builder),
    )

def config(env, builder):
    return Record(
        headers=env.config(config_headers, builder),
    )
