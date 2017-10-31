import fbuild.builders.cxx

def build(ctx):
    builders = fbuild.builders.cxx.guess(ctx, platform_options=[
        ({'msvc++'}, {'flags': ['/EHsc']}),
        ({'posix'}, {'flags': ['-Wall', '-Werror']}),
    ])

    lib = builders.static.build_lib('lib_static', ['lib.cpp'], macros=['STATIC_LINK'])
    exe = builders.static.build_exe('exe_static', ['exe.cpp'], macros=['STATIC_LINK'],
        libs=[lib])

    ctx.logger.log(' * running %s:' % exe)
    builders.static.run([exe])

    lib = builders.shared.build_lib('lib_shared', ['lib.cpp'], macros=['BUILD_LIB'])
    exe = builders.shared.build_exe('exe_shared', ['exe.cpp'], libs=[lib])

    ctx.logger.log(' * running %s:' % exe)
    builders.shared.run([exe])
