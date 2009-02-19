import fbuild
import fbuild.builders.c

def build():
    static = fbuild.builders.c.guess_static()
    lib1 = static.build_lib('static1', ['lib1/lib1.c'])
    lib2 = static.build_lib('static2', ['lib2/lib2.c'],
        includes=['lib1'], libs=[lib1])

    # If you specify the dependent libraries to build_lib, fbuild will
    # automatically add those libraries to the exe libraries.
    exe = static.build_exe('static', ['exe.c'],
        includes=['lib1', 'lib2'], libs=[lib2])

    fbuild.logger.log(' * running %s:' % exe)
    fbuild.execute([exe])

    shared = fbuild.builders.c.guess_shared()
    lib1 = shared.build_lib('shared1', ['lib1/lib1.c'])
    lib2 = shared.build_lib('shared2', ['lib2/lib2.c'],
        includes=['lib1'], libs=[lib1])
    exe = shared.build_exe('shared', ['exe.c'],
        includes=['lib1', 'lib2'], libs=[lib2])

    fbuild.logger.log(' * running %s:' % exe)
    fbuild.execute([exe])
