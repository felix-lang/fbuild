def configure(conf, options):
    from fbuild.builders.ocaml import config
    config(conf)

def build(conf, options):
    import fbuild.packages.ocaml as ocaml

    lib = ocaml.BytecodeLibrary('lib', ['lib*.ml{,i}'])
    exe = ocaml.BytecodeExecutable('exe.byte', ['exe.ml'], libs=[lib])
    exe.build(conf)

    lib = ocaml.NativeLibrary('lib', ['lib*.ml{,i}'])
    exe = ocaml.NativeExecutable('exe.native', ['exe.ml'], libs=[lib])
    exe.build(conf)
