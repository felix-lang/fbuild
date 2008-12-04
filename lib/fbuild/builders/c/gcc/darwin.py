from .. import gcc

# ------------------------------------------------------------------------------

def config_static(*args, **kwargs):
    return gcc.config_static(*args, **kwargs)

def config_shared(*args,
        lib_suffix='.dylib',
        lib_link_flags=['-dynamiclib'],
        **kwargs):
    return gcc.config_shared(
        lib_suffix=lib_suffix,
        lib_link_flags=lib_link_flags,
        *args, **kwargs)
