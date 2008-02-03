from .. import gxx

# -----------------------------------------------------------------------------

def config_shared(*args,
        lib_suffix='.dylib',
        lib_link_flags=['-dynamiclib'],
        **kwargs):
    return gxx.config_shared(
        lib_suffix=lib_suffix,
        lib_link_flags=lib_link_flags,
        *args, **kwargs)


def config(*args, config_shared=config_shared, **kwargs):
    return gxx.config(config_shared=config_shared, *args, **kwargs)
