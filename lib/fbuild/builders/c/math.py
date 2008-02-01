from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def _check(builder, function):
    return builder.check_compile('''
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
        conf.configure('headers.math_h.' + f, _check, conf.static, f)

def config_bsd(conf):
    config_finite(conf)

# -----------------------------------------------------------------------------
# c99 classification macros

def config_fpclassify(conf):
    conf.configure('headers.math_h.fpclassify',
        _check, conf.static, 'fpclassify')

def config_isfinite(conf):
    for f in 'isfinite', 'isfinitef', 'isfinitel':
        conf.configure('headers.math_h.' + f, _check, conf.static, f)

def config_isinf(conf):
    for f in 'isinf', 'isinff', 'isinfl':
        conf.configure('headers.math_h.' + f, _check, conf.static, f)

def config_isnan(conf):
    for f in 'isnan', 'isnanf', 'isnanl':
        conf.configure('headers.math_h.' + f, _check, conf.static, f)

def config_isnormal(conf):
    for f in 'isnormal', 'isnormalf', 'isnormall':
        conf.configure('headers.math_h.' + f, _check, conf.static, f)

def config_signbit(conf):
    conf.configure('headers.math_h.signbit', _check, conf.static, 'signbit')

def config_c99(conf):
    config_fpclassify(conf)
    config_isfinite(conf)
    config_isinf(conf)
    config_isnan(conf)
    config_isnormal(conf)
    config_signbit(conf)

# -----------------------------------------------------------------------------

def config(conf):
    if not conf.static.check_header_exists('math.h'):
        raise ConfigFailed('missing math.h')

    config_bsd(conf)
    config_c99(conf)
