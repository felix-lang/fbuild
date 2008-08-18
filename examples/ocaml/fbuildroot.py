def build(env):
    import fbuild.packages.ocaml as ocaml

    lib = ocaml.BytecodeLibrary('lib', ['lib*.ml{,i}'])
    exe = ocaml.BytecodeExecutable('exe.byte', ['exe.ml'], libs=[lib])
    exe.build(env)

    lib = ocaml.NativeLibrary('lib', ['lib*.ml{,i}'])
    exe = ocaml.NativeExecutable('exe.native', ['exe.ml'], libs=[lib])
    exe.build(env)
