from fbuild import ConfigFailed
import fbuild.builders.platform

# -----------------------------------------------------------------------------

def config(env, **kwargs):
    platform = fbuild.builders.platform.config(env)

    if 'darwin' in platform:
        from .gxx.darwin import config
        return config(env, **kwargs)
    elif 'posix' in platform:
        from .gxx import config
        return config(env, **kwargs)
    elif 'windows' in platform:
        from .msvc import config
        return config(env, **kwargs)
    else:
        raise ConfigFailed('cannot find c++ compiler for %s' % platform)
