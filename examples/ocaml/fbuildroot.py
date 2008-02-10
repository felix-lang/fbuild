def configure(conf, options):
    from fbuild.builders.ocaml import config
    config(conf)

def build(conf, options):
    from fbuild import execute
    import fbuild.packages.ocaml as ocaml

    lib = ocaml.BytecodeLibrary('lib', ['lib.ml'],
        destdir='build')
    exe = ocaml.BytecodeExecutable('exe.byte', ['exe.ml'],
        libs=[lib],
        destdir='build')
    execute(exe.build(conf))

    lib = ocaml.NativeLibrary('lib', ['lib.ml'],
        destdir='build')
    exe = ocaml.NativeExecutable('exe.native', ['exe.ml'],
        libs=[lib],
        destdir='build')
    execute(exe.build(conf))
