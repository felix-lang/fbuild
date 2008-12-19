import fbuild.builders.c.guess
import fbuild.record

# -----------------------------------------------------------------------------

def config_static(*args, **kwargs):
    return fbuild.builders.c.guess.guess_config('c++ static', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_static'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_static'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_static'),
    ], *args, **kwargs)

def config_shared(*args, **kwargs):
    return fbuild.builders.c.guess.guess_config('c++ shared', [
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.config_shared'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.config_shared'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.config_shared'),
    ], *args, **kwargs)

def config(*args, **kwargs):
    return fbuild.record.Record(
        static=config_static(*args, **kwargs),
        shared=config_shared(*args, **kwargs),
    )
