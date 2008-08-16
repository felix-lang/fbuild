import fbuild.builders.c.std as c_std

# -----------------------------------------------------------------------------

default_types_int = c_std.default_types_int + ('bool',)

default_types_float = c_std.default_types_float

default_types_misc = c_std.default_types_misc

default_types = default_types_int + default_types_float + default_types_misc

# -----------------------------------------------------------------------------

def config_types(env):
    return c_std.config_types(env,
        types_int=default_types_int,
        types_float=default_types_float,
        types_misc=default_types_misc)

def config_class_member_initialization(env):
    tests = env.setdefault('tests', {})

    tests['class_member_intialization'] = env['static'].check_compile('''
        struct X {
            static const int i = 1;
        };

        int main(int argc, char** argv) {
            return 0;
        }
    ''', 'checking class member initialization')

def config(env):
    config_types(env)
    config_class_member_initialization(env)
    c_std.config_stddef_h(env)
