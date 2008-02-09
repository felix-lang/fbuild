from . import MissingHeader

# -----------------------------------------------------------------------------

def config_function(conf, function):
    math_h = conf.setdefault('headers', {}).setdefault('math_h', {})
    math_h[function] = conf['static'].check_compile('''
        #include <math.h>
        int main(int argc, char** argv) {
            %s(0.0);
            return 0;
        }
    ''' % function, 'checking if %s is in math.h' % function)

# -----------------------------------------------------------------------------
# bsd functions

def config_finite(conf):
    for f in 'finite', 'finitef', 'finitel':
        config_function(conf, f)

def config_bsd(conf):
    config_finite(conf)

# -----------------------------------------------------------------------------
# c99 classification macros

def config_fpclassify(conf):
    config_function(conf, 'fpclassify')

def config_isfinite(conf):
    for f in 'isfinite', 'isfinitef', 'isfinitel':
        config_function(conf, f)

def config_isinf(conf):
    for f in 'isinf', 'isinff', 'isinfl':
        config_function(conf, f)

def config_isnan(conf):
    for f in 'isnan', 'isnanf', 'isnanl':
        config_function(conf, f)

def config_isnormal(conf):
    for f in 'isnormal', 'isnormalf', 'isnormall':
        config_function(conf, f)

def config_signbit(conf):
    for f in 'signbit', 'signbitf', 'signbitl':
        config_function(conf, f)

def config_c99(conf):
    config_fpclassify(conf)
    config_isfinite(conf)
    config_isinf(conf)
    config_isnan(conf)
    config_isnormal(conf)
    config_signbit(conf)

# -----------------------------------------------------------------------------

def config(conf):
    if not conf['static'].check_header_exists('math.h'):
        raise MissingHeader('math.h')

    config_bsd(conf)
    config_c99(conf)
