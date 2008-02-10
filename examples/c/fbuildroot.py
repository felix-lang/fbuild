def configure(conf, options):
    from fbuild.builders.c.guess import config
    config(conf)

def build(conf, options):
    import fbuild.packages.c as c

    lib = c.SharedLibrary('library', ['lib.c'])
    exe = c.Executable('executable', ['exe.c'], libs=[lib])
    exe.build(conf)
