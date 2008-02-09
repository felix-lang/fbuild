from functools import partial

from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_function(conf, function):
    cmath = conf.setdefault('headers', {}).setdefault('cmath', {})
    cmath['function'] = conf['static'].check_compile('''
        #include <cmath>
        int main(int argc, char** argv) {
            std::%s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in cmath' % function)

def config_fpclassify(conf):
    return config_function(conf, 'fpclassify')

def config_isfinite(conf):
    return config_function(conf, 'isfinite')

def config_isinf(conf):
    return config_function(conf, 'isinf')

def config_isnan(conf):
    return config_function(conf, 'isnan')

def config_isnormal(conf):
    return config_function(conf, 'isnormal')

def config_signbit(conf):
    return config_function(conf, 'signbit')

# -----------------------------------------------------------------------------

def config(conf):
    if not conf['static'].check_header_exists('cmath'):
        raise ConfigFailed('missing cmath')

    config_fpclassify(conf)
    config_isfinite(conf)
    config_isinf(conf)
    config_isnan(conf)
    config_isnormal(conf)
    config_signbit(conf)
