from . import std
from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

default_types_complex = tuple('%s %s' % (typename, suffix)
    for typename in std.default_types_float
    for suffix in ('_Complex', '_Imaginary'))

default_types_bool = ('_Bool',)

default_types = default_types_complex + default_types_bool

default_types_complex_h = ('complex',) + tuple('%s %s' % (typename, suffix)
    for typename in std.default_types_float
    for suffix in ('complex', 'imaginary'))

default_types_stdbool_h = ('bool',)

default_types_stdint_h = tuple('%sint%s%s_t' % (sign, attr, size)
    for sign in ('', 'u')
    for attr in ('', '_least', '_fast')
    for size in (8, 16, 32, 64)) + \
    ('intptr_t', 'uintptr_t', 'intmax_t', 'uintmax_t')

# -----------------------------------------------------------------------------

def detect_types(builder):
    return std.get_types_data(builder, default_types)

def detect_complex_h_types(builder):
    return std.get_types_data(builder, default_types_complex_h,
        headers=['complex.h'])

def detect_stdbool_h_types(builder):
    return std.get_types_data(builder, default_types_stdbool_h,
        headers=['stdbool.h'])

def detect_stdint_h_types(builder):
    return std.get_types_data(builder, default_types_stdint_h,
        headers=['stdint.h'], int_type=True)

# -----------------------------------------------------------------------------

def config_types(conf, builder):
    conf.configure('c99.types', detect_types, builder)

def config_complex_h(conf, builder):
    if not builder.check_header_exists('complex.h'):
        raise ConfigFailed('missing complex.h')

    conf.configure('c99.complex_h.types', detect_complex_h_types, builder)

def config_stdbool_h(conf, builder):
    if not builder.check_header_exists('stdbool.h'):
        raise ConfigFailed('missing stdbool.h')

    conf.configure('c99.stdbool_h.types', detect_stdbool_h_types, builder)

def config_stdint_h(conf, builder):
    if not builder.check_header_exists('stdint.h'):
        raise ConfigFailed('missing stdint.h')

    conf.configure('c99.stdint_h.types', detect_stdint_h_types, builder)

def config(conf, builder):
    config_types(conf, builder)
    config_complex_h(conf, builder)
    config_stdbool_h(conf, builder)
    config_stdint_h(conf, builder)

# -----------------------------------------------------------------------------

def types(conf):
    return (t for t in default_types if t in conf.c99.types)

def types_stdbool_h(conf):
    return (t for t in default_types_stdbool_h if t in conf.c99.stdbool_h.types)

def types_stdint_h(conf):
    return (t for t in default_types_stdint_h if t in conf.c99.stdint_h.types)

def type_aliases_stdint_h(conf):
    try:
        return {t:t for t in types_stdint_h(conf)}
    except AttributeError:
        pass

    # this compiler doesn't support stdint.h, so return some fake aliases
    aliases = std.type_aliases_int(conf)

    d = {}
    for size in 1, 2, 4, 8:
        for sign in '', 'u':
            for attr in '', '_least', '_fast':
                t = '%sint%s%s_t' % (sign, attr, size * 8)
                try:
                    d[t] = aliases[(size, sign == '')]
                except KeyError:
                    pass

    return d
