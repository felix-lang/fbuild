import fbuild.builders.c
import fbuild.db

# ------------------------------------------------------------------------------

@fbuild.db.caches
def guess_static(*args, **kwargs):
    """L{static} tries to guess the static system c++ compiler according to the
    platform. It accepts a I{platform} keyword that overrides the system's
    platform. This can be used to use a non-default compiler. Any extra
    arguments and keywords are passed to the compiler's configuration
    functions."""

    return fbuild.builders.c._guess_builder('c++ static', (
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.static'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.static'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.static'),
    ), *args, **kwargs)

@fbuild.db.caches
def guess_shared(*args, **kwargs):
    """L{shared} tries to guess the shared system c++ compiler according to the
    platform. It accepts a I{platform} keyword that overrides the system's
    platform. This can be used to use a non-default compiler. Any extra
    arguments and keywords are passed to the compiler's configuration
    functions."""

    return fbuild.builders.c._guess_builder('c++ shared', (
        ({'darwin'}, 'fbuild.builders.cxx.gxx.darwin.shared'),
        ({'posix'}, 'fbuild.builders.cxx.gxx.shared'),
        ({'windows'}, 'fbuild.builders.cxx.msvc.shared'),
    ), *args, **kwargs)
