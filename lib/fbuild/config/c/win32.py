import fbuild
import fbuild.builders.c
import fbuild.config.c as c
import fbuild.temp

# ------------------------------------------------------------------------------

class windows_h(c.Header):
    @c.cacheproperty
    def LoadLibrary(self):
        # try to get a shared compiler
        shared = fbuild.builders.c.guess_shared()

        lib_code = '''
            #ifdef __cplusplus
            extern "C" {
            #endif
            int fred(int argc, char** argv) { return 0; }
            #ifdef __cplusplus
            }
            #endif
        '''

        exe_code = '''
            #include <windows.h>
            #include <stdlib.h>

            int main(int argc,char** argv) {
                HMODULE lib = LoadLibrary(%s);
                void *fred;
                if(!lib) return 1;
                fred = (void*)GetProcAddress(lib,"fred");
                if(!fred) return 1;
                return 0;
            }
        '''

        fbuild.logger.check("checking LoadLibrary in 'windows.h'")

        with fbuild.temp.tempfile(lib_code, self.builder.src_suffix) as lib_src:
            try:
                obj = shared.uncached_compile(lib_src, quieter=1)
                lib = shared.uncached_link_lib(lib_src.parent / 'temp', [obj],
                    quieter=1)
            except fbuild.ExecutionError:
                pass
            else:
                if self.builder.try_run(exe_code % lib, quieter=1):
                    fbuild.logger.passed()
                    return c.Function('HMODULE', 'char*')

            fbuild.logger.failed()
            return None

    def GetProcAddress(self):
        if self.LoadLibrary:
            return c.Function('void*', 'HMODULE', 'char*')
