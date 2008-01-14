from fbuild.builders import find_program
from ...c import gcc

# -----------------------------------------------------------------------------

def config_static(conf, *, exe=None, **kwargs):
    return gcc.config_static(conf,
        src_suffix='.cc',
        exe=exe or find_program(conf, 'g++', 'c++'),
        **kwargs)


def config_shared(conf, *, exe=None, **kwargs):
    return gcc.config_shared(conf,
        src_suffix='.cc',
        exe=exe or find_program(conf, 'g++', 'c++'),
        **kwargs)

def config(conf, *args, **kwargs):
    config_static(conf, *args, **kwargs)
    config_shared(conf, *args, **kwargs)
