from fbuild.builders.c.gcc import darwin
from fbuild.builders.cxx import gxx

# -----------------------------------------------------------------------------

def config_shared(*args, src_suffix='.cc', **kwargs):
    return darwin.config_shared(src_suffix=src_suffix, *args, **kwargs)

def config(*args, config_shared=config_shared, **kwargs):
    return gxx.config(config_shared=config_shared, *args, **kwargs)
