import fbuild.db
from fbuild.builders.c import MissingHeader
from fbuild.record import Record

# -----------------------------------------------------------------------------

@fbuild.db.caches
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

def config_fpclassify(builder):
    return _config_function(builder, 'fpclassify')

def config_isfinite(builder):
    return _config_function(builder, 'isfinite')

def config_isinf(builder):
    return _config_function(builder, 'isinf')

def config_isnan(builder):
    return _config_function(builder, 'isnan')

def config_isnormal(builder):
    return _config_function(builder, 'isnormal')

def config_signbit(builder):
    return _config_function(builder, 'signbit')

# -----------------------------------------------------------------------------

def config(builder):
    if not builder.check_header_exists('cmath'):
        raise MissingHeader('cmath')

    record = Record()
    record.update(config_fpclassify(builder))
    record.update(config_isfinite(builder))
    record.update(config_isinf(builder))
    record.update(config_isnan(builder))
    record.update(config_isnormal(builder))
    record.update(config_signbit(builder))

    return record
