from . import std, MissingHeader

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

def config_types(env):
    c99 = env.setdefault('c99', {})
    c99['types'] = std.get_types_data(env['static'], default_types)

def config_complex_h(env):
    static = env['static']
    if not static.check_header_exists('complex.h'):
        raise c.MissingHeader('complex.h')

    complex_h = env.setdefault('headers', {}).setdefault('complex_h', {})
    complex_h['types'] = std.get_types_data(static, default_types_complex_h,
        headers=['complex.h'])

def config_stdbool_h(env):
    static = env['static']
    if not static.check_header_exists('stdbool.h'):
        raise c.MissingHeader('stdbool.h')

    stdbool_h = env.setdefault('headers', {}).setdefault('stdbool_h', {})
    stdbool_h['types'] = std.get_types_data(static, default_types_stdbool_h,
        headers=['stdbool.h'])

def config_stdint_h(env):
    static = env['static']
    if not static.check_header_exists('stdint.h'):
        raise c.MissingHeader('stdint.h')

    stdint_h = env.setdefault('headers', {}).setdefault('stdint_h', {})
    stdint_h['types'] = std.get_types_data(static, default_types_stdint_h,
        headers=['stdint.h'], int_type=True)

# -----------------------------------------------------------------------------

def config_stdio_h(env):
    stdio_h = env.setdefault('headers', {}).setdefault('stdio_h', {})

    static = env['static']
    stdio_h['snprintf'] = static.check_run('''
        #include <stdio.h>

        int main(int argc,char** argv) {
            char s[50];
            int n = snprintf(s, 50, "%d %s\\n", 12345, "hello!");
            return n!=13;
        }
    ''', 'checking if snprintf is in stdio.h')

    stdio_h['vsnprintf'] = static.check_run('''
        #include <stdio.h>
        #include <stdarg.h>

        int check(char const*fmt,...)
        {
            va_list ap;
            va_start(ap,fmt);
            int n = vsnprintf(NULL,0,fmt,ap);
            va_end(ap);
            return n!=3;
        }

        int main(int argc,char** argv) {
            return check("%s","XXX"); // 0 means pass
        }
    ''', 'checking if vsnprintf is in stdio.h')

# -----------------------------------------------------------------------------

def config(env):
    config_stdio_h(env)
    config_types(env)
    config_complex_h(env)
    config_stdbool_h(env)
    config_stdint_h(env)

# -----------------------------------------------------------------------------

def types(env):
    return (t for t in default_types if t in env['c99']['types'])

def types_stdbool_h(env):
    types = env['headers']['stdbool_h']['types']
    return (t for t in default_types_stdbool_h if t in types)

def types_stdint_h(env):
    types = env['headers']['stdint_h']['types']
    return (t for t in default_types_stdint_h if t in types)

def type_aliases_stdint_h(env):
    try:
        return {t:t for t in types_stdint_h(env)}
    except AttributeError:
        pass

    # this compiler doesn't support stdint.h, so return some fake aliases
    aliases = std.type_aliases_int(env)

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
