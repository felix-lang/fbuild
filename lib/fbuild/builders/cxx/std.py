import fbuild.builders.c.std as c_std
import fbuild.db
from fbuild import ConfigFailed
from fbuild.record import Record
from fbuild.builders.c import MissingHeader

# -----------------------------------------------------------------------------

default_types_int = c_std.default_types_int + ('bool',)

default_types_float = c_std.default_types_float

default_types_misc = c_std.default_types_misc

default_types = default_types_int + default_types_float + default_types_misc

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_types(ctx, builder):
    return c_std.config_types(builder,
        types_int=default_types_int,
        types_float=default_types_float,
        types_misc=default_types_misc)

# -----------------------------------------------------------------------------

@fbuild.db.caches
def config_compiler_bugs(ctx, builder):
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
        stddef_h=c_std.config_stddef_h(builder),
    )

def config(builder):
    return Record(
        types=config_types(builder),
        headers=config_headers(builder),
        bugs=config_compiler_bugs(builder),
    )
