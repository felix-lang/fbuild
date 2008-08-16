from fbuild import ConfigFailed

# -----------------------------------------------------------------------------

def config(env, *, platform=None, **kwargs):
    platform = env.config('fbuild.builders.platform.config', platform)

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
