from fbuild.builders.c import guess_static

def configure(ctx):
    return guess_static(ctx, platform_options=[
        ({'posix'}, {'flags+': ['-std=c99']})
    ])

def build(ctx):
    c = configure(ctx)
    return c.build_lib('mylib', ['mylib.c'])
