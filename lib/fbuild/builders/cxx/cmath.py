from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# -----------------------------------------------------------------------------

def _config_function(builder, function):
    record = Record()

    record[function] = builder.check_compile('''
        #include <cmath>
        int main(int argc, char** argv) {
            std::%s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in cmath' % function)

    return record

def config_fpclassify(env, builder):
    return _config_function(builder, 'fpclassify')

def config_isfinite(env, builder):
    return _config_function(builder, 'isfinite')

def config_isinf(env, builder):
    return _config_function(builder, 'isinf')

def config_isnan(env, builder):
    return _config_function(builder, 'isnan')

def config_isnormal(env, builder):
    return _config_function(builder, 'isnormal')

def config_signbit(env, builder):
    return _config_function(builder, 'signbit')

# -----------------------------------------------------------------------------

def config(env, builder):
    if not builder.check_header_exists('cmath'):
        raise MissingHeader('cmath')

    record = Record()
    record.update(config_fpclassify(env, builder))
    record.update(config_isfinite(env, builder))
    record.update(config_isinf(env, builder))
    record.update(config_isnan(env, builder))
    record.update(config_isnormal(env, builder))
    record.update(config_signbit(env, builder))

    return record
