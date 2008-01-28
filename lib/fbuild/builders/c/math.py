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

def config_finite(conf, builder):
    for f in 'finite', 'finitef', 'finitel':
        conf.configure('math_h.' + f, _check, builder, f)

def config_bsd(conf, builder):
    config_finite(conf, builder)

# -----------------------------------------------------------------------------
# c99 classification macros

def config_isfinite(conf, builder):
    for f in 'isfinite', 'isfinitef', 'isfinitel':
        conf.configure('math_h.' + f, _check, builder, f)

def config_isinf(conf, builder):
    for f in 'isinf', 'isinff', 'isinfl':
        conf.configure('math_h.' + f, _check, builder, f)

def config_isnan(conf, builder):
    for f in 'isnan', 'isnanf', 'isnanl':
        conf.configure('math_h.' + f, _check, builder, f)

def config_isnormal(conf, builder):
    for f in 'isnormal', 'isnormalf', 'isnormall':
        conf.configure('math_h.' + f, _check, builder, f)

def config_fpclassify(conf, builder):
    conf.configure('math_h.fpclassify', _check, builder, 'fpclassify')

def config_signbit(conf, builder):
    conf.configure('math_h.signbit', _check, builder, 'signbit')

def config_signbit(conf, builder):
    conf.configure('math_h.signbit', _check, builder, 'signbit')

def config_c99(conf, builder):
    config_isfinite(conf, builder)
    config_isinf(conf, builder)
    config_isnan(conf, builder)
    config_fpclassify(conf, builder)

# -----------------------------------------------------------------------------

def config(conf, builder):
    if not builder.check_header_exists('math.h'):
        raise ConfigFailed('missing math.h')

    config_bsd(conf, builder)
    config_c99(conf, builder)
