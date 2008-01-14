import fbuild.builders

# -----------------------------------------------------------------------------

class Linker(fbuild.builders.Builder):
    yaml_state = ('ar', 'ranlib', 'prefix', 'suffix', 'color')

    def __init__(self, system, ar, ranlib, *,
            prefix='',
            suffix='',
            color=None):
        super().__init__(system)

        self.ar = ar
        self.ranlib = ranlib
        self.prefix = prefix
        self.suffix = suffix
        self.color = color

        self._ar_cmd = None

    def _get_ar_cmd(self):
        self._ar_cmd = fbuild.builders.SimpleCommand(
            self.system, self.ar, self.prefix, self.suffix,
            color=self.color,
        )

        return self._ar_cmd

    def __call__(self, *args, **kwargs):
        ar_cmd = self._ar_cmd or self._get_ar_cmd()

        lib = ar_cmd(*args, **kwargs)

        if self.ranlib is not None:
            self.system.execute(self.ranlib + [lib],
                (' '.join(self.ranlib), lib),
                color=self.color,
                quieter=kwargs.get('quieter', 0),
            )

        return lib

# -----------------------------------------------------------------------------

def make(system, *,
        ar=None,
        ranlib=None,
        lib_prefix='',
        lib_suffix='',
        **kwargs):
    ar = ar or fbuild.builders.find_program(system, 'ar')
    ranlib = ranlib or fbuild.builders.find_program(system, 'ranlib')

    return Linker(system, [ar, 'rc'], [ranlib] if ranlib else None,
        **kwargs)

def config(conf, *, **kwargs):
    conf.configure('ar', make, conf.system, **kwargs)
