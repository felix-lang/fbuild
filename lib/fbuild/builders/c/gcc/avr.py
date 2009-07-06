import fbuild.builders.ar.avr
import fbuild.builders.c.gcc

# ------------------------------------------------------------------------------

class Gcc(fbuild.builders.c.gcc.Gcc):
    """Overload Gcc's builder to add the avr-gcc options."""

    def __init__(self, *args, mmcu, pre_flags=[], **kwargs):
        self.mmcu = mmcu

        pre_flags = list(pre_flags)
        pre_flags.append('-mmcu=' + mmcu)

        super().__init__(*args, pre_flags=pre_flags, **kwargs)

# ------------------------------------------------------------------------------

def make_gcc(exe=None, default_exes=['avr-gcc'], **kwargs):
    return Gcc(
        fbuild.builders.find_program([exe] if exe else default_exes),
        **kwargs)

def make_compiler(*args, make_gcc=make_gcc, **kwargs):
    return fbuild.builders.gcc.make_compiler(*args, make_gcc=make_gcc, **kwargs)

def make_linker(*args, make_gcc=make_gcc, **kwargs):
    return fbuild.builders.gcc.make_linker(*args, make_gcc=make_gcc, **kwargs)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def static(*args, make_gcc=make_gcc, **kwargs):
    return fbuild.builders.c.gcc.static(*args,
        make_gcc=make_gcc,
        make_lib_linker=fbuild.builders.ar.avr.Ar,
        cross_compiler=True,
        **kwargs)

@fbuild.db.caches
def shared(*args, make_gcc=make_gcc, **kwargs):
    return fbuild.builders.c.gcc.shared(*args,
        make_gcc=make_gcc,
        cross_compiler=True,
        **kwargs)
