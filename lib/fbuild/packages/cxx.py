from fbuild.packages import c

# -----------------------------------------------------------------------------

class _Object(c._Object):
    _default_builder = 'fbuild.builders.cxx.guess.config'

class StaticObject(_Object):
    def command(self, conf, *args, **kwargs):
        return self._builder(conf).static.compile(*args, **kwargs)

class SharedObject(_Object):
    def command(self, conf, *args, **kwargs):
        return self._builder(conf).shared.compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(c._Linker):
    _default_builder = 'fbuild.builders.cxx.guess.config'

class StaticLibrary(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return self._builder(conf).static.compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return self._builder(conf).static.link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return self._builder(conf).shared.compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return self._builder(conf).shared.link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, conf, *args, **kwargs):
        return self._builder(conf).static.compile(*args, **kwargs)

    def command(self, conf, *args, **kwargs):
        return self._builder(conf).static.link_exe(*args, **kwargs)
