from . import MissingHeader

# -----------------------------------------------------------------------------

def config_function(env, function):
    math_h = env.setdefault('headers', {}).setdefault('math_h', {})
    math_h[function] = env['static'].check_compile('''
        #include <math.h>
        int main(int argc, char** argv) {
            %s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in math.h' % function)

# -----------------------------------------------------------------------------
# bsd functions

def config_finite(env):
    for f in 'finite', 'finitef', 'finitel':
        config_function(env, f)

def config_bsd(env):
    config_finite(env)

# -----------------------------------------------------------------------------
# c99 classification macros

def config_fpclassify(env):
    config_function(env, 'fpclassify')

def config_isfinite(env):
    for f in 'isfinite', 'isfinitef', 'isfinitel':
        config_function(env, f)

def config_isinf(env):
    for f in 'isinf', 'isinff', 'isinfl':
        config_function(env, f)

def config_isnan(env):
    for f in 'isnan', 'isnanf', 'isnanl':
        config_function(env, f)

def config_isnormal(env):
    for f in 'isnormal', 'isnormalf', 'isnormall':
        config_function(env, f)

def config_signbit(env):
    for f in 'signbit', 'signbitf', 'signbitl':
        config_function(env, f)

def config_c99(env):
    config_fpclassify(env)
    config_isfinite(env)
    config_isinf(env)
    config_isnan(env)
    config_isnormal(env)
    config_signbit(env)

# -----------------------------------------------------------------------------

def config(env):
    if not env['static'].check_header_exists('math.h'):
        raise MissingHeader('math.h')

    config_bsd(env)
    config_c99(env)
