from fbuild import Record
from . import MissingHeader

# -----------------------------------------------------------------------------

def _config_functions(builder, *functions):
    record = Record()

    for function in functions:
        record[function] = builder.check_compile('''
            #include <math.h>
            int main(int argc, char** argv) {
                %s(0.0);
                return 0;
            }
        ''' % function, 'checking if %s is in math.h' % function)

    return record

# -----------------------------------------------------------------------------
# bsd functions

def config_finite(env, builder):
    return _config_functions(builder, 'finite', 'finitef', 'finitel')

def config_bsd(env, builder):
    return config_finite(env, builder)

# -----------------------------------------------------------------------------
# c99 classification macros

def config_fpclassify(env, builder):
    return _config_functions(builder, 'fpclassify')

def config_isfinite(env, builder):
    return _config_functions(builder, 'isfinite', 'isfinitef', 'isfinitel')

def config_isinf(env, builder):
    return _config_functions(builder, 'isinf', 'isinff', 'isinfl')

def config_isnan(env, builder):
    return _config_functions(builder, 'isnan', 'isnanf', 'isnanl')

def config_isnormal(env, builder):
    return _config_functions(builder, 'isnormal', 'isnormalf', 'isnormall')

def config_signbit(env, builder):
    return _config_functions(builder, 'signbit', 'signbitf', 'signbitl')

def config_c99(env, builder):
    record = Record()
    record.update(config_fpclassify(env, builder))
    record.update(config_isfinite(env, builder))
    record.update(config_isinf(env, builder))
    record.update(config_isnan(env, builder))
    record.update(config_isnormal(env, builder))
    record.update(config_signbit(env, builder))

    return record

# -----------------------------------------------------------------------------

def config(env, builder):
    if not builder.check_header_exists('math.h'):
        raise MissingHeader('math.h')

    record = Record()
    record.update(config_bsd(env, builder))
    record.update(config_c99(env, builder))

    return record
