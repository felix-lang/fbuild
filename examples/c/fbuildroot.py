import fbuild.packages.c as c

lib = c.SharedLibrary('library', ['lib.c'])
exe = c.Executable('executable', ['exe.c'], libs=[lib])

def build():
    exe.build()
