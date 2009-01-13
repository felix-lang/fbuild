import fbuild.builders.c

def build():
    static = fbuild.builders.c.guess_static()
    shared = fbuild.builders.c.guess_shared()

    lib = static.build_lib('static', ['lib.c'])
    exe = static.build_exe('static', ['exe.c'], libs=[lib])

    lib = shared.build_lib('shared', ['lib.c'])
    exe = shared.build_exe('shared', ['exe.c'], libs=[lib])
