"""This module extends the C 1999 math.h header with common extensions."""

import fbuild.config.c as c
import fbuild.config.c.c99 as c99

# ------------------------------------------------------------------------------

class math_h(c99.math_h):
    finite = c.function_test('int', 'double')
    finitef = c.function_test('int', 'float')
    finitel = c.function_test('int', 'long double')
    isinf = c.function_test('int', 'double')
    isinff = c.function_test('int', 'float')
    isinfl = c.function_test('int', 'long double')
    isnan = c.function_test('int', 'double')
    isnanf = c.function_test('int', 'float')
    isnanl = c.function_test('int', 'long double')
