import fbuild.db
from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# ------------------------------------------------------------------------------

@fbuild.db.caches
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

# ------------------------------------------------------------------------------
# bsd functions

def config_finite(builder):
    return _config_functions(builder, 'finite', 'finitef', 'finitel')

def config_bsd(builder):
    return config_finite(builder)

# ------------------------------------------------------------------------------
# c99 classification macros

def config_fpclassify(builder):
    return _config_functions(builder, 'fpclassify')

def config_isfinite(builder):
    return _config_functions(builder, 'isfinite', 'isfinitef', 'isfinitel')

def config_isinf(builder):
    return _config_functions(builder, 'isinf', 'isinff', 'isinfl')

def config_isnan(builder):
    return _config_functions(builder, 'isnan', 'isnanf', 'isnanl')

def config_isnormal(builder):
    return _config_functions(builder, 'isnormal', 'isnormalf', 'isnormall')

def config_signbit(builder):
    return _config_functions(builder, 'signbit', 'signbitf', 'signbitl')

def config_c99(builder):
    record = Record()
    record.update(config_fpclassify(builder))
    record.update(config_isfinite(builder))
    record.update(config_isinf(builder))
    record.update(config_isnan(builder))
    record.update(config_isnormal(builder))
    record.update(config_signbit(builder))

    return record

# ------------------------------------------------------------------------------

def config(builder):
    if not builder.check_header_exists('math.h'):
        raise MissingHeader('math.h')

    record = Record()
    record.update(config_bsd(builder))
    record.update(config_c99(builder))

    return record
