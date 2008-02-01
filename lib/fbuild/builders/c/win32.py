from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_LoadLibrary(conf):
    conf.configure('windows_h.LoadLibrary', conf.static.check_compile, '''
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

def config(conf):
    if not conf.static.check_header_exists('windows.h'):
        raise ConfigFailed('cannot find windows.h')

    config_LoadLibrary(conf)
