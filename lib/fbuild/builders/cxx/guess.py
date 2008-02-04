from fbuild import ConfigFailed
import fbuild.builders.platform

# -----------------------------------------------------------------------------

def config(conf, **kwargs):
    platform = fbuild.builders.platform.config(conf)

    if 'darwin' in platform:
        from .gxx.darwin import config
        return config(conf, **kwargs)
    elif 'posix' in platform:
        from .gxx import config
        return config(conf, **kwargs)
    elif 'windows' in platform:
        from .msvc import config
        return config(conf, **kwargs)
    else:
        raise ConfigFailed('cannot find c++ compiler for %s' % platform)
