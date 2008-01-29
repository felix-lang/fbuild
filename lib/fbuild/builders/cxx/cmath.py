from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def _check(builder, function):
    return builder.check_compile('''
        #include <math.h>
        int main(int argc, char** argv) {
            %s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in cmath' % function)

# -----------------------------------------------------------------------------

def config_fpclassify(conf, builder):
    conf.configure('cmath.fpclassify', _check, builder, 'fpclassify')

def config_isfinite(conf, builder):
    conf.configure('cmath.isfinite', _check, builder, 'isfinite')

def config_isinf(conf, builder):
    conf.configure('cmath.isinf', _check, builder, 'isinf')

def config_isnan(conf, builder):
    conf.configure('cmath.isnan', _check, builder, 'isnan')

def config_isnormal(conf, builder):
    conf.configure('cmath.isnormal', _check, builder, 'isnormal')

def config_signbit(conf, builder):
    conf.configure('cmath.signbit', _check, builder, 'signbit')

# -----------------------------------------------------------------------------

def config(conf, builder):
    if not builder.check_header_exists('cmath'):
        raise ConfigFailed('missing cmath')

    config_fpclassify(conf, builder)
    config_isfinite(conf, builder)
    config_isinf(conf, builder)
    config_isnan(conf, builder)
    config_isnormal(conf, builder)
    config_signbit(conf, builder)
