import fbuild.builders.ar

# ------------------------------------------------------------------------------

class Ar(fbuild.builder.ar.Ar):
    def __init__(self, exe='avr-ar', ranlib='avr-ranlib', **kwargs):
        super().__init__(exe, ranlib=ranlib, **kwargs)
