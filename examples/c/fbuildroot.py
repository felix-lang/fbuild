import fbuild
import fbuild.builders.c
import os

def build(ctx):
    builders = fbuild.builders.c.guess(ctx)

    lib1 = builders.static.build_lib('static1', ['lib1/lib1.c'], macros=['STATIC_LINK'])
    lib2 = builders.static.build_lib('static2', ['lib2/lib2.c'], macros=['STATIC_LINK'],
        includes=['lib1'], libs=[lib1])

    # If you specify the dependent libraries to build_lib, fbuild will
    # automatically add those libraries to the exe libraries.
    exe = builders.static.build_exe('static', ['exe.c'], macros=['STATIC_LINK'],
        includes=['lib1', 'lib2'], libs=[lib2])

    ctx.logger.log(' * running %s:' % exe)
    builders.static.run([exe])

    lib1 = builders.shared.build_lib('shared1', ['lib1/lib1.c'], macros=['BUILD_LIB1'])
    lib2 = builders.shared.build_lib('shared2', ['lib2/lib2.c'], macros=['BUILD_LIB2'],
        includes=['lib1'], libs=[lib1])
    exe = builders.shared.build_exe('shared',
        [fbuild.path.Path.abspath('exe.c')], # test absolute paths
        includes=['lib1', 'lib2'], libs=[lib2])

    ctx.logger.log(' * running %s:' % exe)
    builders.shared.run([exe])
