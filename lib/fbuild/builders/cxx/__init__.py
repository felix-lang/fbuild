import fbuild.builders.c

# ------------------------------------------------------------------------------


guess = fbuild.builders.c.Guesser('c++', {'msvc++', 'g++', 'clang++', 'icpc'}, (
        ({'windows', 'msvc++'}, 'fbuild.builders.cxx.msvc.static',
                     'fbuild.builders.cxx.msvc.shared'),
        ({'iphone', 'simulator', 'g++'},
            'fbuild.builders.cxx.gxx.iphone.static_simulator',
            'fbuild.builders.cxx.gxx.iphone.shared_simulator'),
        ({'iphone', 'g++'}, 'fbuild.builders.cxx.gxx.iphone.static',
                            'fbuild.builders.cxx.gxx.iphone.shared'),
        ({'darwin', 'clang++'}, 'fbuild.builders.cxx.clangxx.darwin.static',
                                'fbuild.builders.cxx.clangxx.darwin.shared'),
        ({'darwin', 'g++'}, 'fbuild.builders.cxx.gxx.darwin.static',
                            'fbuild.builders.cxx.gxx.darwin.shared'),
        ({'clang++'}, 'fbuild.builders.cxx.clangxx.static',
                      'fbuild.builders.cxx.clangxx.shared'),
        ({'g++'}, 'fbuild.builders.cxx.gxx.static',
                  'fbuild.builders.cxx.gxx.static'),
        ({'icpc'}, 'fbuild.builders.cxx.intelxx.static',
                   'fbuild.builders.cxx.intelxx.shared'),
    ))


@fbuild.builders.c._guess_deprecated
def guess_static(ctx, **kwargs):
    return guess.static(ctx, **kwargs)

@fbuild.builders.c._guess_deprecated
def guess_shared(ctx, **kwargs):
    return guess.shared(ctx, **kwargs)
