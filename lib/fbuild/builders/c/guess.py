from fbuild import ConfigFailed, env
from fbuild.record import Record

# -----------------------------------------------------------------------------

def guess_config(name, functions, *args, platform=None, **kwargs):
    platform = env.cache('fbuild.builders.platform.config', platform)

    for subplatform, function in functions:
        if subplatform <= platform:
            return env.cache(function, *args, **kwargs)

    raise ConfigFailed('cannot find a %s builder for %s' % (name, platform))

# -----------------------------------------------------------------------------

def config_static(*args, **kwargs):
    return guess_config('c static', [
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.config_static'),
        ({'posix'}, 'fbuild.builders.c.gcc.config_static'),
        ({'windows'}, 'fbuild.builders.c.msvc.config_static'),
    ], *args, **kwargs)

def config_shared(*args, **kwargs):
    return guess_config('c shared', [
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.config_shared'),
        ({'posix'}, 'fbuild.builders.c.gcc.config_shared'),
        ({'windows'}, 'fbuild.builders.c.msvc.config_shared'),
    ], *args, **kwargs)

def config(*args, **kwargs):
    return Record(
        static=env.cache(config_static, *args, **kwargs),
        shared=env.cache(config_shared, *args, **kwargs),
    )
