import fbuild.builders.ar.avr
import fbuild.builders.c.gcc

# ------------------------------------------------------------------------------

class Gcc(fbuild.builders.c.gcc):
    """Overload Gcc's builder to add the avr-gcc options."""

    def __init__(*args, mmcu=None, **kwargs):
        self.mmcu = mmcu

        super().__init__(*args, **kwargs)

    def __call__(*args, mmcu=None, flags=[], **kwargs):
        flags = list(flags)

        mmcu = self.mmcu if mmcu is None else mmcu
        if mmcu is not None:
            flags.extend(('-mmcu', mmcu))

        return super().__call__(*args, flags=flags, **kwargs)

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
        **kwargs)

@fbuild.db.caches
def shared(*args, make_gcc=make_gcc, **kwargs):
    return fbuild.builders.c.gcc.shared(*args,
        make_gcc=make_gcc,
        **kwargs)
