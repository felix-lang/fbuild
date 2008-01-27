from itertools import chain

from fbuild.builders.c import tempfile
from fbuild import ExecutionError, ConfigFailed

# -----------------------------------------------------------------------------

def get_int_types():
    types = []
    for prefix in ('', 'signed ', 'unsigned '):
        for i in ('char', 'short', 'int', 'long', 'long long'):
            types.append('%s%s' % (prefix, i))

    return types

def get_float_types():
    return ['float', 'double', 'long double']

def get_misc_types():
    return ['void*']

def get_types():
    return get_int_types() + get_float_types() + get_misc_types()

def get_stddef_types():
    return ['size_t', 'wchar_t', 'ptrdiff_t']

# -----------------------------------------------------------------------------

def get_type_data(builder, typename, *args, int_type=False, **kwargs):
    builder.check('getting type %r info' % typename)

    code = '''
        #include <stddef.h>
        #include <stdio.h>

        typedef %s type;
        struct TEST { char c; type mem; };
        int main(int argc, char** argv) {
            printf("%%d\\n", (int)offsetof(struct TEST, mem));
            printf("%%d\\n", (int)sizeof(type));
        #ifdef INTTYPE
            printf("%%d\\n", (type)~3 < (type)0);
        #endif
            return 0;
        }
    ''' % typename

    if int_type:
        cflags = dict(kwargs.get('cflags', {}))
        cflags['macros'] = cflags.get('macros', []) + ['INTTYPE=1']
        kwargs['cflags'] = cflags

    try:
        data = builder.tempfile_run(code, *args, **kwargs)[0].split()
    except ExecutionError:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to discover type data for %r' % typename)

    d = {'alignment': int(data[0]), 'size': int(data[1])}
    s = 'alignment: %(alignment)s size: %(size)s'

    if int_type:
        d['sign'] = int(data[2]) == 1
        s += ' sign: %(sign)s'

    builder.log(s % d, color='green')

    return d


def get_types_data(builder, types, *args, **kwargs):
    d = {}
    for t in types:
        try:
            d[t] = get_type_data(builder, t, *args, **kwargs)
        except ConfigFailed:
            pass

    return d


def get_type_conversions(builder, type_pairs, *args, **kwargs):
    lines = []
    for t1, t2 in type_pairs:
        lines.append(
            'printf("%%d %%d\\n", '
            '(int)sizeof((%(t1)s)0 + (%(t2)s)0), '
            '(%(t1)s)~3 + (%(t2)s)1 < (%(t1)s)0 + (%(t2)s)0);' %
            {'t1': t1, 't2': t2})

    code = '''
    #include <stdio.h>

    int main(int argc, char** argv) {
        %s
        return 0;
    }
    ''' % '\n'.join(lines)

    try:
        data = builder.tempfile_run(code, *args, **kwargs)[0]
    except ExecutionError:
        builder.log('failed', color='yellow')
        raise ConfigFailed('failed to detect type conversions for %s' % types)

    d = {}
    for line, (t1, t2) in zip(data.decode('utf-8').split('\n'), type_pairs):
        size, sign = line.split()
        d[(t1, t2)] = (int(size), int(sign) == 1)

    return d

# -----------------------------------------------------------------------------

def detect_types(builder):
    if not builder.check_header_exists('stddef.h'):
        raise ConfigFailed('missing stddef.h')

    d = {}
    for typename in get_int_types():
        try:
            d[typename] = get_type_data(builder, typename, int_type=True)
        except ConfigFailed:
            pass

    for typename in get_float_types() + get_misc_types():
        try:
            d[typename] = get_type_data(builder, typename)
        except ConfigFailed:
            pass

    return d

def detect_int_type_conversions(builder):
    builder.check('getting int type conversions')
    types = get_int_types()
    type_pairs = [(t1, t2) for t1 in types for t2 in types]
    try:
        d = get_type_conversions(builder, type_pairs)
    except ConfigFailed:
        builder.log('failed', color='yellow')
    else:
        builder.log('ok', color='green')

    return d


def detect_stddef(builder):
    return get_types_data(builder, get_stddef_types())

# -----------------------------------------------------------------------------

def config_types(conf, builder):
    conf.configure('types', detect_types, builder)
    conf.configure('int_conversions', detect_int_type_conversions, builder)

def config_stddef(conf, builder):
    conf.configure('stddef.types', detect_stddef, builder)

def config(conf, builder):
    conf.subconfigure('std', config_types, builder)
    conf.subconfigure('std', config_stddef, builder)

# -----------------------------------------------------------------------------

def get_int_aliases(conf):
    d = {}
    for t in get_int_types():
        try:
            data = conf.std.types[t]
        except KeyError:
            pass
        else:
            d.setdefault((data['size'], data['sign']), t)

    return d


def get_int_conversion_aliases(conf):
    aliases = get_int_aliases(conf)
    d = {}
    for type_pair, size_sign in conf.std.int_conversions.items():
        print(type_pair, size_sign)
        d[type_pair] = aliases[size_sign]
    return d
