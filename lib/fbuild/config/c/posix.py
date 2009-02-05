"""fbuild.config.c.posix extends fbuild.config.c.posix04 to expose cross
platform flags and libraries, and exposes many common extensions."""

from fbuild.config.c.posix04 import *

# ------------------------------------------------------------------------------

class dlfcn_h(dlfcn_h):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Linux needs to link against libdl for dl* support.
        if 'linux' in self.platform:
            self.external_libs.append('dl')

class pthread_h(pthread_h):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'linux' in self.platform:
            self.external_libs.append('pthread')

        # Solaris needs to link against librt for posix support.
        elif 'solaris' in self.platform:
            self.external_libs.append('rt')
