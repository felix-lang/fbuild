def configure(conf, options):
    from fbuild.builders.c.guess import config
    config(conf)

def build(conf, options):
    import fbuild.packages as packages
    import fbuild.packages.c as c

    lib = c.SharedLibrary('library', ['lib.c'],
        destdir='build')
    exe = c.Executable('executable', ['exe.c'],
        libs=[lib],
        destdir='build')
    exe.build(conf)
