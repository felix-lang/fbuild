from . import Builder, SimpleCommand, find_program

# -----------------------------------------------------------------------------

#@fbuild.system.system_cache
def find_ar_exe(system, exe_names=None):
    if exe_names is None:
        exe_names = ['ar']
    return find_program(system, exe_names)


#@fbuild.system.system_cache
def find_ranlib_exe(system, exe_names=None):
    if exe_names is None:
        exe_names = ['ranlib']
    return find_program(system, exe_names)


class Ar(SimpleCommand):
    def __init__(self, system, ar, ranlib, *args, **kwargs):
        super().__init__(system, ar, *args, **kwargs)

        self.ranlib = ranlib

    def __call__(self, system, *args, **kwargs):
        lib = super().__call__(*args, **kwargs)

        if self.ranlib is not None:
            system.execute(self.ranlib + [lib],
                (' '.join(self.ranlib), lib),
                color=self.color,
            )

        return lib

    def __repr__(self):
        return '%s(ar=%r, ranlib=%r)' % (
            self.__class__.__name__,
            self.exe,
            self.ranlib,
        )


#@fbuild.system.system_cache
def config_link_staticlib2(system, *args, **kwargs):
    ar = [find_ar_exe(system), 'rc']
    ranlib = find_ranlib_exe(system)

    if ranlib is not None:
        ranlib = [ranlib]

    return Ar(system, ar, ranlib, *args, **kwargs)

class config_link_staticlib(Builder):
    def __init__(self, system,
            ar=None, ranlib=None,
            prefix='', suffix='',
            color='cyan'):

        if ar is None:
            ar = [find_ar_exe(system), 'rc']

        if ranlib is None:
            ranlib = find_ranlib_exe(system)

            if ranlib is not None:
                ranlib = [ranlib]

        self.state = dict(
            ar=ar,
            ranlib=ranlib,
            prefix=prefix,
            suffix=suffix,
            color=color,
        )

    def __call__(self, system):
        return Ar(system, **self.state)
