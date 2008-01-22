from .. import gcc as Gcc

# -----------------------------------------------------------------------------

def make_shared(gcc,
        lib_suffix='.dylib',
        lib_link_flags=['-dynamiclib'],
        **kwargs):
    return Gcc.make_shared(gcc,
        lib_suffix=lib_suffix,
        lib_link_flags=lib_link_flags,
        **kwargs)

# -----------------------------------------------------------------------------

def config(conf, exe, make_shared=make_shared, **kwargs):
    return Gcc.config(conf, exe, make_shared=make_shared, **kwargs)
