import fbuild.config.c as c

# ------------------------------------------------------------------------------

class omp_h(c.Header):
    omp_get_thread_num = c.function_test('int', 'void')
