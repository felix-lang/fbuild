def configure(env, options):
    from fbuild.builders.c.guess import config
    config(env)

def build(env, options):
    import fbuild.packages.c as c

    lib = c.SharedLibrary('library', ['lib.c'])
    exe = c.Executable('executable', ['exe.c'], libs=[lib])
    exe.build(env)
