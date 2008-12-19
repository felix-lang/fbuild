import fbuild
import fbuild.builders.cxx.guess

def build():
    cxx = fbuild.builders.cxx.guess.config()

    lib = cxx.static.build_lib('lib_static', ['lib.cpp'])
    exe = cxx.static.build_exe('exe_static', ['exe.cpp'], libs=[lib])

    lib = cxx.shared.build_lib('lib_shared', ['lib.cpp'])
    exe = cxx.shared.build_exe('exe_shared', ['exe.cpp'], libs=[lib])
