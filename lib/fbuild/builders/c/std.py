
# -----------------------------------------------------------------------------

def detect_type_size(system, builder, typedef, headers=[], suffix='.c'):
    if not typedef.startswith('typedef'):
        typedef = 'typedef %s t;' % typedef

    code = '''
        %s
        int main(int argc, char** argv) {
            printf("%%d\\n", (int)sizeof(t));
            return 0;
        }
    ''' % typedef

    headers = ['stddef.h', 'stdio.h'] + headers

    try:
        with builder.tempfile(system, code, headers, suffix=suffix) as src:
            objects = builder.compile(system, [src])
            exe = builder.link_exe(system, objects)
            return int(system.execute([exe]))
    except ExecutionError:
        return None



def detect_type_alignment():
    pass

def detect_type_sign():
    pass

def detect_type_aliases():
    pass

def detect_type_sizes(system, builder, types):
    pass


def detect_types(group, builder, types):
    for t in types:
        g = group.make_config_subgroup(t.replace(' ', '_'))
        g.configure('size',      detect_type_size,      builder, t)
        g.configure('alignment', detect_type_alignment, builder, t)
        g.configure('sign',      detect_type_sign,      builder, t)
        g.configure('alias',     detect_type_alias,     builder, t)

def detect_std_types(group, builder):
    #std_types = group.make_config_subgroup('std.types')

    ints = ['char', 'short', 'int', 'long', 'long long']
    signed_ints = ['signed ' + t for t in ints]
    unsigned_ints = ['unsigned ' + t for t in ints]
    types = ints + signed_ints + unsigned_ints + ['bool', 'float', 'double']

# -----------------------------------------------------------------------------

def detect_endian(group, builder):
    pass

def detect_isnan():
    pass

def detect_vsnprintf():
    pass
