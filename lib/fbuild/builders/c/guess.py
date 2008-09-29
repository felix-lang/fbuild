from fbuild import ConfigFailed
from fbuild.record import Record

# -----------------------------------------------------------------------------

def guess_config(env, name, functions, *args, platform=None, **kwargs):
    platform = env.config('fbuild.builders.platform.config', platform)

    for subplatform, function in functions:
        if subplatform <= platform:
            return env.config(function, *args, **kwargs)

    raise ConfigFailed('cannot find a %s builder for %s' % (name, platform))

# -----------------------------------------------------------------------------

def config_static(env, *args, **kwargs):
    return guess_config(env, 'c static', [
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.config_static'),
        ({'posix'}, 'fbuild.builders.c.gcc.config_static'),
        ({'windows'}, 'fbuild.builders.c.msvc.config_static'),
    ], *args, **kwargs)

def config_shared(env, *args, **kwargs):
    return guess_config(env, 'c shared', [
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.config_shared'),
        ({'posix'}, 'fbuild.builders.c.gcc.config_shared'),
        ({'windows'}, 'fbuild.builders.c.msvc.config_shared'),
    ], *args, **kwargs)

def config(env, *args, **kwargs):
    return Record(
        static=env.config(config_static, *args, **kwargs),
        shared=env.config(config_shared, *args, **kwargs),
    )
