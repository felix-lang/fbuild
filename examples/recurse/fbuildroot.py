from fbuild.builders.c import guess_static

def configure(ctx):
    c = guess_static(ctx)
    ctx.recurse('mylib', 'configure')
    return c

def build(ctx):
    c = configure(ctx)
    mylib = ctx.recurse('mylib')
    c.build_exe('x', ['x.c'], libs=[mylib])
