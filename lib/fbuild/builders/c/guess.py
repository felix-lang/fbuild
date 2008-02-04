from fbuild import ConfigFailed
import fbuild.builders.platform

# -----------------------------------------------------------------------------

def config(conf, **kwargs):
    platform = fbuild.builders.platform.config(conf)

    if 'darwin' in platform:
        from .gcc.darwin import config
        return config(conf, **kwargs)
    elif 'posix' in platform:
        from .gcc import config
        return config(conf, **kwargs)
    elif 'windows' in platform:
        from .msvc import config
        return config(conf, **kwargs)
    else:
        raise ConfigFailed('cannot find c compiler for %s' % platform)
