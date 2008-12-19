import fbuild
import fbuild.builders.platform
import fbuild.functools
import fbuild.record

# -----------------------------------------------------------------------------

def guess_config(name, functions, db, *args, platform=None, **kwargs):
    platform = fbuild.builders.platform.config(db, platform)

    for subplatform, function in functions:
        if subplatform <= platform:
            return fbuild.functools.call(function, db, *args, **kwargs)

    raise fbuild.ConfigFailed('cannot find a %s builder for %s' %
        (name, platform))

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
    return fbuild.record.Record(
        static=config_static(*args, **kwargs),
        shared=config_shared(*args, **kwargs),
    )
