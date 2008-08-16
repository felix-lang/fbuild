from . import MissingHeader

# -----------------------------------------------------------------------------

def config_builder(env, builder):
    if not env[builder].check_header_exists('omp.h'):
        raise MissingHeader('omp.h')

    code = '''
        #include <omp.h>
        #include <stdio.h>
        #include <stdlib.h>

        int main (int argc, char *argv[]) {
            int nthreads, tid;

            #pragma omp parallel private(nthreads, tid)
            {
                tid = omp_get_thread_num();
                printf("Hello World from thread = %d\n", tid);

                /* Only master thread does this */
                if (tid == 0) {
                    nthreads = omp_get_num_threads();
                    printf("Number of threads = %d\n", nthreads);
                }
            }
        }
    '''

    logger.check('checking if supports omp_get_thread_num')
    for flags in [], ['-openmp'], ['-fopenmp'], ['/openmp']:
        if env[builder].try_run(code, lflags={'flags': flags}):
            logger.passed('ok %r' % ' '.join(flags))

            omp_h = env.setdefault('headers', {}) \
                       .setdefault('omp_h', {}) \
                       .setdefault('flags', {})
            omp_h[builder] = flags
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to link openmp program')

def config_static(env):
    config_builder(env, 'static')

def config_shared(env):
    config_builder(env, 'shared')

def config(env):
    config_static(env)
    config_shared(env)
