from . import std
from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def get_types():
    types = ['_Bool']
    for float_type in std.get_float_types():
        for attr in '_Complex', '_Imaginary':
            types.append('%s %s' % (float_type, attr))

    return types


def get_complex_types():
    types = ['complex']

    for float_type in std.get_float_types():
        types.append('%s complex' % float_type)

    return types


def get_stdbool_types():
    return ['bool']


def get_stdint_types():
    types = []
    for sign in '', 'u':
        for attr in '', '_least', '_fast':
            for size in 8, 16, 32, 64:
                types.append('%sint%s%s_t' % (sign, attr, size))

    types.append('intptr_t')
    types.append('uintptr_t')
    types.append('intmax_t')
    types.append('uintmax_t')

    return types

# -----------------------------------------------------------------------------

def detect_types(builder):
    return std.get_types_data(builder, get_types())

def detect_complex(builder):
    if not builder.check_header_exists('complex.h'):
        raise ConfigFailed('missing complex.h')

    return std.get_types_data(builder, get_complex_types(),
        headers=['complex.h'])

def detect_stdbool(builder):
    if not builder.check_header_exists('stdbool.h'):
        raise ConfigFailed('missing stdbool.h')

    return std.get_types_data(builder, get_stdbool_types(),
        headers=['stdbool.h'])

def detect_stdint(builder):
    if not builder.check_header_exists('stdint.h'):
        raise ConfigFailed('missing stdint.h')

    return std.get_types_data(builder, get_stdint_types(),
        headers=['stdint.h'],
        int_type=True)

# -----------------------------------------------------------------------------

def config_types(conf, builder):
    conf.configure('types', detect_types, builder)

def config_complex(conf, builder):
    conf.configure('complex.types', detect_complex, builder)

def config_stdbool(conf, builder):
    conf.configure('stdbool.types', detect_stdbool, builder)

def config_stdint(conf, builder):
    conf.configure('stdint.types', detect_stdint, builder)

def config(conf, builder):
    conf.subconfigure('c99', config_types, builder)
    conf.subconfigure('c99', config_complex, builder)
    conf.subconfigure('c99', config_stdbool, builder)
    conf.subconfigure('c99', config_stdint, builder)

# -----------------------------------------------------------------------------

def get_fake_stdint_types(conf):
    try:
        types = conf.c99.stdint.types
    except AttributeError:
        pass
    else:
        return {t:t for t in get_stdint_types() if t in types}

    aliases = std.get_int_aliases(conf)

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
