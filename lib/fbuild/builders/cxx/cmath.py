from functools import partial

from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config_function(env, function):
    cmath = env.setdefault('headers', {}).setdefault('cmath', {})
    cmath[function] = env['static'].check_compile('''
        #include <cmath>
        int main(int argc, char** argv) {
            std::%s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in cmath' % function)

def config_fpclassify(env):
    return config_function(env, 'fpclassify')

def config_isfinite(env):
    return config_function(env, 'isfinite')

def config_isinf(env):
    return config_function(env, 'isinf')

def config_isnan(env):
    return config_function(env, 'isnan')

def config_isnormal(env):
    return config_function(env, 'isnormal')

def config_signbit(env):
    return config_function(env, 'signbit')

# -----------------------------------------------------------------------------

def config(env):
    if not env['static'].check_header_exists('cmath'):
        raise ConfigFailed('missing cmath')

    config_fpclassify(env)
    config_isfinite(env)
    config_isinf(env)
    config_isnan(env)
    config_isnormal(env)
    config_signbit(env)
