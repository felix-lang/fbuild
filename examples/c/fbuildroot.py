import fbuild

def build():
    c = fbuild.env.cache('fbuild.builders.c.guess.config')

    lib = c.static.build_lib('static', ['lib.c'])
    exe = c.static.build_exe('static', ['exe.c'], libs=[lib])

    lib = c.shared.build_lib('shared', ['lib.c'])
    exe = c.shared.build_exe('shared', ['exe.c'], libs=[lib])
