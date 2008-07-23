from . import MissingHeader

# -----------------------------------------------------------------------------

def config_builder(conf, builder):
    if not conf[builder].check_header_exists('omp.h'):
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
        if conf[builder].try_run(code, lflags={'flags': flags}):
            logger.passed('ok %r' % ' '.join(flags))

            omp_h = conf.setdefault('headers', {}) \
                        .setdefault('omp_h', {}) \
                        .setdefault('flags', {})
            omp_h[builder] = flags
            break
    else:
        logger.failed()
        raise ConfigFailed('failed to link openmp program')

def config_static(conf):
    config_builder(conf, 'static')

def config_shared(conf):
    config_builder(conf, 'shared')

def config(conf):
    config_static(conf)
    config_shared(conf)
