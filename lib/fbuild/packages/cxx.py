from fbuild.packages import c

# -----------------------------------------------------------------------------

class _Object(c._Object):
    default_config = 'fbuild.builders.cxx.guess.config'

class StaticObject(_Object):
    def command(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

class SharedObject(_Object):
    def command(self, *args, **kwargs):
        return self.config.shared.compile(*args, **kwargs)

# -----------------------------------------------------------------------------

class _Linker(c._Linker):
    default_config = 'fbuild.builders.cxx.guess.config'

class StaticLibrary(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.static.link_lib(*args, **kwargs)

class SharedLibrary(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.shared.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.shared.link_lib(*args, **kwargs)

class Executable(_Linker):
    def compiler(self, *args, **kwargs):
        return self.config.static.compile(*args, **kwargs)

    def command(self, *args, **kwargs):
        return self.config.static.link_exe(*args, **kwargs)
