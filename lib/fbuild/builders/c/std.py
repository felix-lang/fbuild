from itertools import chain

from fbuild import ConfigFailed, ExecutionError, env, logger
from fbuild.record import Record
from fbuild.builders.c import MissingHeader

# -----------------------------------------------------------------------------

# Since the 'char' type can be signed or unsigned, put the type first so that
# the 'signed char' or 'unsigned char' will have precidence over the ambigous
# 'char' type.
default_types_int = ('signed char', 'unsigned char', 'char')

default_types_int += tuple('%s%s' % (prefix, typename)
    for prefix in ('', 'signed ', 'unsigned ')
    for typename in ('short', 'int', 'long', 'long long'))

default_types_float = ('float', 'double', 'long double')

default_types_misc = ('void*',)

default_types = default_types_int + default_types_float + default_types_misc

default_types_stddef_h = ('size_t', 'wchar_t', 'ptrdiff_t')

# -----------------------------------------------------------------------------

def get_type_data(builder, typename, *args,
        int_type=False,
        headers=[],
        **kwargs):
    logger.check('getting type %r info' % typename)

    code = '''
        #include <stddef.h>
        #include <stdio.h>
        %s

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
    ''' % ('\n'.join('#include <%s>' % h for h in headers), typename)

    if int_type:
        ckwargs = dict(kwargs.get('ckwargs', {}))
        ckwargs['macros'] = ckwargs.get('macros', []) + ['INTTYPE=1']
        kwargs['ckwargs'] = ckwargs

    try:
        data = builder.tempfile_run(code, *args, **kwargs)[0].split()
    except ExecutionError:
        logger.failed()
        raise ConfigFailed('failed to discover type data for %r' % typename)

    d = {'alignment': int(data[0]), 'size': int(data[1])}
    s = 'alignment: %(alignment)s size: %(size)s'

    if int_type:
        d['signed'] = int(data[2]) == 1
        s += ' signed: %(signed)s'

    logger.passed(s % d)

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
        raise ConfigFailed('failed to detect type conversions for %s' % types)

    d = {}
    for line, (t1, t2) in zip(data.decode('utf-8').split('\n'), type_pairs):
        size, sign = line.split()
        d[(t1, t2)] = (int(size), int(sign) == 1)

    return d

# -----------------------------------------------------------------------------

def config_types(builder,
        types_int=default_types_int,
        types_float=default_types_float,
        types_misc=default_types_misc):
    types = get_types_data(builder, types_int, int_type=True)
    types.update(get_types_data(builder, types_float))
    types.update(get_types_data(builder, types_misc))
    types['enum'] = get_type_data(builder, 'enum enum_t {tag}')

    return types

def config_int_type_conversions(builder, types_int=default_types_int):
    pairs = [(t1, t2) for t1 in types_int for t2 in types_int]

    logger.check('getting int type conversions')
    try:
        int_type_conversions = get_type_conversions(builder, pairs)
    except ConfigFailed as e:
        logger.failed()
        raise e from e

    logger.passed()
    return int_type_conversions

def config_stddef_h(builder):
    if not builder.check_header_exists('stddef.h'):
        raise MissingHeader('stddef.h')

    types = get_types_data(builder, default_types_stddef_h, int_type=True)
    return Record(types=types)

def config_headers(builder):
    return Record(stddef_h=env.cache(config_stddef_h, builder))

def config(builder):
    return Record(
        types=env.cache(config_types, builder),
        int_type_conversions=env.cache(config_int_type_conversions, builder),
        headers=env.cache(config_headers, builder))

# -----------------------------------------------------------------------------

def types_int(builder):
    types = env.cache(config_types, builder)
    return (t for t in default_types_int if t in types)

def types_float(builder):
    types = env.cache(config_types, builder)
    return (t for t in default_types_float if t in types)

def type_aliases_int(builder):
    types = env.cache(config_types, builder)
    d = {}
    for t in types_int(builder):
        data = types[t]
        d.setdefault((data['size'], data['signed']), t)

    return d

def type_aliases_float(builder):
    types = env.cache(config_types, builder)
    d = {}
    for t in types_float(builder):
        data = types[t]
        d.setdefault(data['size'], t)

    return d

def type_conversions_int(builder):
    aliases = env.cache(type_aliases_int, builder)
    int_type_conversions = env.cache(config_int_type_conversions, builder)
    return {type_pair: aliases[size_signed]
        for type_pair, size_signed in int_type_conversions.items()}
