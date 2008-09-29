import fbuild.builders.c.std as c_std
from fbuild import env
from fbuild.record import Record

# -----------------------------------------------------------------------------

default_types_int = c_std.default_types_int + ('bool',)

default_types_float = c_std.default_types_float

default_types_misc = c_std.default_types_misc

default_types = default_types_int + default_types_float + default_types_misc

# -----------------------------------------------------------------------------

def config_types(builder):
    return c_std.config_types(builder,
        types_int=default_types_int,
        types_float=default_types_float,
        types_misc=default_types_misc)

def config_compiler_bugs(builder):
    """
    Test for common c++ bugs.
    """

    bugs = Record()
    bugs.class_member_intialization = builder.check_compile('''
        struct X {
            static const int i = 1;
        };

        int main(int argc, char** argv) {
            return 0;
        }
    ''', 'checking class member initialization')

    return bugs

def config_headers(builder):
    return Record(
        stddef_h=env.cache(c_std.config_stddef_h, builder),
    )

def config(builder):
    return Record(
        types=env.cache(config_types, builder),
        headers=env.cache(config_headers, builder),
        bugs=env.cache(config_compiler_bugs, builder),
    )
