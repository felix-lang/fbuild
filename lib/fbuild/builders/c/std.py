from itertools import chain

import fbuild.db
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

def get_type_data(ctx, builder, typename, *args,
        int_type=False,
        headers=[],
        **kwargs):
    ctx.logger.check('getting type %r info' % typename)

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
    except fbuild.ExecutionError:
        ctx.logger.failed()
        raise fbuild.ConfigFailed('failed to discover type data for %r' %
            typename)

    d = {'alignment': int(data[0]), 'size': int(data[1])}
    s = 'alignment: %(alignment)s size: %(size)s'

    if int_type:
        d['signed'] = int(data[2]) == 1
        s += ' signed: %(signed)s'

    ctx.logger.passed(s % d)

    return d


def get_types_data(ctx, builder, types, *args, **kwargs):
    d = {}
    for t in types:
        try:
            d[t] = get_type_data(ctx, builder, t, *args, **kwargs)
        except fbuild.ConfigFailed:
            pass

    return d


def get_type_conversions(ctx, builder, type_pairs, *args, **kwargs):
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
    except fbuild.ExecutionError:
        raise fbuild.ConfigFailed('failed to detect type conversions for %s' %
            types)

    d = {}
    for line, (t1, t2) in zip(data.decode('utf-8').split('\n'), type_pairs):
        size, sign = line.split()
        d[(t1, t2)] = (int(size), int(sign) == 1)

    return d

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_types(ctx, builder,
        types_int=default_types_int,
        types_float=default_types_float,
        types_misc=default_types_misc):
    types = get_types_data(ctx, builder, types_int, int_type=True)
    types.update(get_types_data(ctx, builder, types_float))
    types.update(get_types_data(ctx, builder, types_misc))
    types['enum'] = get_type_data(ctx, builder, 'enum enum_t {tag}')

    return types

@fbuild.db.caches
def config_int_type_conversions(ctx, builder, types_int=default_types_int):
    pairs = [(t1, t2) for t1 in types_int for t2 in types_int]

    ctx.logger.check('getting int type conversions')
    try:
        int_type_conversions = get_type_conversions(ctx, builder, pairs)
    except fbuild.ConfigFailed as e:
        ctx.logger.failed()
        raise e from e

    ctx.logger.passed()
    return int_type_conversions

@fbuild.db.caches
def config_stddef_h(ctx, builder):
    if not builder.check_header_exists('stddef.h'):
        raise MissingHeader('stddef.h')

    types = get_types_data(enbv, builder, default_types_stddef_h, int_type=True)
    return Record(types=types)

def config_headers(builder):
    return Record(stddef_h=config_stddef_h(builder))

def config(builder):
    return Record(
        types=config_types(builder),
        int_type_conversions=config_int_type_conversions(builder),
        headers=config_headers(builder))

# -----------------------------------------------------------------------------

def types_int(builder):
    types = config_types(builder)
    return (t for t in default_types_int if t in types)

def types_float(builder):
    types = config_types(builder)
    return (t for t in default_types_float if t in types)

def type_aliases_int(builder):
    types = config_types(builder)
    d = {}
    for t in types_int(builder):
        data = types[t]
        d.setdefault((data['size'], data['signed']), t)

    return d

def type_aliases_float(builder):
    types = config_types(builder)
    d = {}
    for t in types_float(builder):
        data = types[t]
        d.setdefault(data['size'], t)

    return d

def type_conversions_int(builder):
    aliases = type_aliases_int(builder)
    int_type_conversions = config_int_type_conversions(builder)
    return {type_pair: aliases[size_signed]
        for type_pair, size_signed in int_type_conversions.items()}
