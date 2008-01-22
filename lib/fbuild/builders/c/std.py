from itertools import chain

from fbuild.builders.c import tempfile
from fbuild import ExecutionError, ConfigFailed

# -----------------------------------------------------------------------------

def get_int_types():
    for prefix in ('', 'signed ', 'unsigned '):
        for i in ('char', 'short', 'int', 'long', 'long long'):
            yield '%s%s' % (prefix, i)

def get_float_types():
    yield 'float'
    yield 'double'
    yield 'long double'

def get_misc_types():
    yield 'void'

def get_types():
    for t in chain(get_int_types(), get_float_types(), get_misc_types()):
        yield t

# -----------------------------------------------------------------------------

def detect_type_data(builder, typename, *args, int_type=False, **kwargs):
    builder.check('getting type %r info' % typename)

    if not typename.startswith('typename'):
        typename = 'typedef %s t;' % typename

    code = '''
        #include <stddef.h>
        #include <stdio.h>

        %s
        struct TEST { char c; t mem; };
        int main(int argc, char** argv) {
            printf("%%d\\n", (int)offsetof(struct TEST, mem));
            printf("%%d\\n", (int)sizeof(t));
            #ifdef INTTYPE
            printf("%%d\\n", (t)~3 < (t)0);
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
        builder.log(code, verbose=1)
        raise ConfigFailed('failed to discover type data for %r' % typename)

    d = dict(
        alignment=int(data[0]),
        size=int(data[1])
    )
    s = 'alignment: %(alignment)s size: %(size)s'

    if int_type:
        d['sign'] = int(data[2]) == 1
        s += ' sign: %(sign)s'

    builder.log(s % d, color='green')

    return d

# -----------------------------------------------------------------------------

def detect_types(builder):
    d = {}
    for t in get_int_types():
        try:
            d[t] = detect_type_data(builder, t, int_type=True)
        except ConfigFailed:
            pass

    for t in chain(get_float_types(), get_misc_types()):
        try:
            d[t] = detect_type_data(builder, t)
        except ConfigFailed:
            pass

    return d


def detect_stddef(builder):
    if not builder.check_header_exists('stddef.h'):
        raise ConfigFailed('missing stddef.h')

    d = {}
    for t in 'size_t', 'wchar_t', 'ptrdiff_t':
        try:
            d[t] = detect_type_data(builder, t, headers=['stddef.h'])
        except ConfigFailed:
            pass

    return d

# -----------------------------------------------------------------------------

def config_types(conf, builder):
    conf.configure('types', detect_types, builder)

def config_stddef(conf, builder):
    conf.configure('stddef', detect_stddef, builder)

def config(conf, builder):
    conf.subconfigure('std', config_types, builder)
    conf.subconfigure('std', config_stddef, builder)

# -----------------------------------------------------------------------------

def get_int_aliases(conf):
    aliases = {}
    for t in get_int_types():
        try:
            data = conf.std.types[t]
        except KeyError:
            pass
        else:
            aliases.setdefault((data['size'] * 8, data['sign']), t)

    return aliases
