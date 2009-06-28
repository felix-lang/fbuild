import fbuild.builders.ar.avr
import fbuild.builders.c.gcc
import fbuild.builders.c.gcc.avr

# ------------------------------------------------------------------------------

def make_gxx(exe=None, default_exes=['avr-g++'], **kwargs):
    return fbuild.builders.c.gcc.avr.make_gcc(exe, default_exes, **kwargs)

def make_compiler(*args, make_gcc=make_gxx, **kwargs):
    return fbuild.builders.gcc.avr.make_compiler(*args,
        make_gcc=make_gcc,
        **kwargs)

def make_linker(*args, make_gcc=make_gxx, **kwargs):
    return fbuild.builders.gcc.avr.make_linker(*args,
        make_gcc=make_gcc,
        **kwargs)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def static(*args, make_gcc=make_gcc, src_suffix='.cc', **kwargs):
    return fbuild.builders.c.gcc.static(*args,
        make_gcc=make_gcc,
        make_lib_linker=fbuild.builders.ar.avr.Ar,
        src_suffix=src_suffix,
        **kwargs)

@fbuild.db.caches
def shared(*args, make_gcc=make_gcc, src_suffix='.cc', **kwargs):
    return fbuild.builders.c.gcc.shared(*args,
        make_gcc=make_gcc,
        src_suffix=src_suffix,
        **kwargs)
