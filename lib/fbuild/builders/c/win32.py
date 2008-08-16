from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config(env, builder):
    if not builder.check_header_exists('windows.h'):
        raise ConfigFailed('cannot find windows.h')

    windows_h = env.setdefault('headers', {}).setdefault('windows_h', {})
    windows_h['LoadLibrary'] = builder.check_compile('''
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
