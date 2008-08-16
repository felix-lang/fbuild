from fbuild import Record
from fbuild.builders.c.guess import guess_config

# -----------------------------------------------------------------------------

def config_static(env, *args, **kwargs):
    return guess_config(env, 'c++ static', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_static'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_static'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_static'),
    ], *args, **kwargs)

def config_shared(env, *args, **kwargs):
    return guess_config(env, 'c++ shared', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_shared'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_shared'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_shared'),
    ], *args, **kwargs)

def config(env, *args, **kwargs):
    return Record(
        static=env.config(config_static, *args, **kwargs),
        shared=env.config(config_shared, *args, **kwargs),
    )
