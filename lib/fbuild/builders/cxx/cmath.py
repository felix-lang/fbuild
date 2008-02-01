from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def _check(builder, function):
    return builder.check_compile('''
        #include <cmath>
        int main(int argc, char** argv) {
            std::%s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in cmath' % function)

# -----------------------------------------------------------------------------

def config_fpclassify(conf):
    conf.configure('headers.cmath.fpclassify',
        _check, conf.static, 'fpclassify')

def config_isfinite(conf):
    conf.configure('headers.cmath.isfinite', _check, conf.static, 'isfinite')

def config_isinf(conf):
    conf.configure('headers.cmath.isinf', _check, conf.static, 'isinf')

def config_isnan(conf):
    conf.configure('headers.cmath.isnan', _check, conf.static, 'isnan')

def config_isnormal(conf):
    conf.configure('headers.cmath.isnormal', _check, conf.static, 'isnormal')

def config_signbit(conf):
    conf.configure('headers.cmath.signbit', _check, conf.static, 'signbit')

# -----------------------------------------------------------------------------

def config(conf):
    if not conf.static.check_header_exists('cmath'):
        raise ConfigFailed('missing cmath')

    config_fpclassify(conf)
    config_isfinite(conf)
    config_isinf(conf)
    config_isnan(conf)
    config_isnormal(conf)
    config_signbit(conf)
