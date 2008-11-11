from fbuild import ConfigFailed, env, logger
from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# -----------------------------------------------------------------------------

def config_omp_h(builder):
    if not builder.check_header_exists('omp.h'):
        raise MissingHeader('omp.h')

    code = r'''
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

            return 0;
        }
    '''

    logger.check('checking if supports omp_get_thread_num')
    for flags in [], ['-openmp'], ['-fopenmp'], ['/openmp']:
        if builder.try_run(code, lkwargs={'flags': flags}):
            logger.passed('ok %r' % ' '.join(flags))

            return Record(flags=flags)
    else:
        logger.failed()
        raise ConfigFailed('failed to link openmp program')


def config(builder):
    return Record(
        headers=Record(
            omp_h=env.cache(config_omp_h, builder),
        )
    )
