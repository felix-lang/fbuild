from fbuild.builders.c import guess

def build(ctx):
    c = guess.static(ctx)
    exe = c.build_exe('x', ['x.c'])
    ctx.install(exe, 'bin')
    ctx.install('doc.txt', 'share', 'some_subdir_of_usr_share')
