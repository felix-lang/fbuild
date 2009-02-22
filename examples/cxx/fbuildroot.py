import fbuild.builders.cxx

def build():
    static = fbuild.builders.cxx.guess_static()
    lib = static.build_lib('lib_static', ['lib.cpp'], macros=['STATIC_LINK'])
    exe = static.build_exe('exe_static', ['exe.cpp'], macros=['STATIC_LINK'],
        libs=[lib])

    fbuild.logger.log(' * running %s:' % exe)
    fbuild.execute([exe])

    shared = fbuild.builders.cxx.guess_shared()
    lib = shared.build_lib('lib_shared', ['lib.cpp'], macros=['BUILD_LIB'])
    exe = shared.build_exe('exe_shared', ['exe.cpp'], libs=[lib])

    fbuild.logger.log(' * running %s:' % exe)
    fbuild.execute([exe])
