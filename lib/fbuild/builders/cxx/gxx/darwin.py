from .. import gxx

# -----------------------------------------------------------------------------

def config_static(conf, *args, **kwargs):
    return gxx.config_static(conf, *args, **kwargs)

def config_shared(conf, *,
        lib_suffix='.dylib',
        lib_link_flags=['-dynamiclib'],
        **kwargs):
    return gxx.config_shared(conf,
        lib_suffix=lib_suffix,
        lib_link_flags=lib_link_flags,
        **kwargs)

def config(conf, *args, **kwargs):
    config_static(conf, *args, **kwargs)
    config_shared(conf, *args, **kwargs)
