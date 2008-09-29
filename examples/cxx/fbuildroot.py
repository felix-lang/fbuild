import fbuild.packages.cxx as cxx

lib = cxx.SharedLibrary('library', ['lib.cpp'])
exe = cxx.Executable('executable', ['exe.cpp'], libs=[lib])

def build():
    exe.build()
