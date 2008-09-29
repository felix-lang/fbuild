from fbuild import env
from fbuild.builders.c.guess import guess_config
from fbuild.record import Record

# -----------------------------------------------------------------------------

def config_static(*args, **kwargs):
    return guess_config('c++ static', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_static'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_static'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_static'),
    ], *args, **kwargs)

def config_shared(*args, **kwargs):
    return guess_config('c++ shared', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_shared'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_shared'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_shared'),
    ], *args, **kwargs)

def config(*args, **kwargs):
    return Record(
        static=env.cache(config_static, *args, **kwargs),
        shared=env.cache(config_shared, *args, **kwargs),
    )
