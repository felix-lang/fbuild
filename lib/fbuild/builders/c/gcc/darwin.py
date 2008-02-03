from .. import gcc

# -----------------------------------------------------------------------------

def config_shared(*args,
        lib_suffix='.dylib',
        lib_link_flags=['-dynamiclib'],
        **kwargs):
    return gcc.config_shared(
        lib_suffix=lib_suffix,
        lib_link_flags=lib_link_flags,
        *args, **kwargs)

def config(*args, config_shared=config_shared, **kwargs):
    return gcc.config(config_shared=config_shared, *args, **kwargs)
