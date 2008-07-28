def configure(conf, options):
    from fbuild.builders.cxx.guess import config
    config(conf)

def build(conf, options):
    import fbuild.packages.cxx as cxx

    lib = cxx.SharedLibrary('library', ['lib.cpp'])
    exe = cxx.Executable('executable', ['exe.cpp'], libs=[lib])
    exe.build(conf)
