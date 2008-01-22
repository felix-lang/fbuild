from . import std
from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def get_types():
    for float_type in std.get_float_types():
        for attr in '_Complex', '_Imaginary':
            yield '%s %s' % (float_type, attr)

    yield '_Bool'

def get_stdint_types():
    for sign in '', 'u':
        for attr in '', '_least', '_fast':
            for size in 8, 16, 32, 64:
                yield '%sint%s%s_t' % (sign, attr, size)

    yield 'intptr_t'
    yield 'uintptr_t'
    yield 'intmax_t'
    yield 'uintmax_t'

# -----------------------------------------------------------------------------

def detect_types(builder):
    d = {}

    for t in get_types():
        try:
            d[t] = std.detect_type_data(builder, t)
        except ConfigFailed:
            pass

    return d


def detect_stdbool(builder):
    if not builder.check_header_exists('stdbool.h'):
        raise ConfigFailed('missing stdbool.h')

    d = {}
    try:
        d['bool'] = std.detect_type_data(builder, 'bool',
            headers=['stdbool.h'])
    except ConfigFailed:
        pass

    return d

def detect_stdint(builder):
    if not builder.check_header_exists('stdint.h'):
        raise ConfigFailed('missing stdint.h')

    d = {}
    for t in get_stdint_types():
        try:
            d[t] = std.detect_type_data(builder, t,
                headers=['stdint.h'],
                int_type=True,
            )
        except ConfigFailed:
            pass

    return d

# -----------------------------------------------------------------------------

def config_types(conf, builder):
    conf.configure('types', detect_types, builder)

def config_stdbool(conf, builder):
    conf.configure('stdbool', detect_stdbool, builder)

def config_stdint(conf, builder):
    conf.configure('stdint', detect_stdint, builder)

def config(conf, builder):
    conf.subconfigure('c99', config_types, builder)
    conf.subconfigure('c99', config_stdbool, builder)
    conf.subconfigure('c99', config_stdint, builder)

# -----------------------------------------------------------------------------

def fake_stdint_types(conf):
    #try:
    #    return {t:t for t in get_stdint_types() if t in conf.c99.stdint}
    #except AttributeError:
    #    pass

    aliases = std.get_int_aliases(conf)

    d = {}
    for size in 8, 16, 32, 64:
        for sign in '', 'u':
            for attr in '', '_least', '_fast':
                t = '%sint%s%s_t' % (sign, attr, size)
                try:
                    d[t] = aliases[(size, sign == '')]
                except KeyError:
                    pass

    return d
