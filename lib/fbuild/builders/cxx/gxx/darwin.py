from fbuild.builders.c.gcc import darwin
from fbuild.builders.cxx import gxx

# -----------------------------------------------------------------------------

def config_static(*args, **kwargs):
    return gxx.config_static(*args, **kwargs)

def config_shared(*args, src_suffix='.cc', **kwargs):
    return darwin.config_shared(
        config_gcc=gxx.config_gxx,
        src_suffix=src_suffix,
        *args, **kwargs)
