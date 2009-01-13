import fbuild.builders.cxx

def build():
    static = fbuild.builders.cxx.guess_static()
    shared = fbuild.builders.cxx.guess_shared()

    lib = static.build_lib('lib_static', ['lib.cpp'])
    exe = static.build_exe('exe_static', ['exe.cpp'], libs=[lib])

    lib = shared.build_lib('lib_shared', ['lib.cpp'])
    exe = shared.build_exe('exe_shared', ['exe.cpp'], libs=[lib])
