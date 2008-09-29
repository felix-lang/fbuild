import fbuild.packages.ocaml as ocaml

blib = ocaml.BytecodeLibrary('lib', ['lib*.ml{,i}'])
bexe = ocaml.BytecodeExecutable('exe.byte', ['exe.ml'], libs=[blib])

nlib = ocaml.NativeLibrary('lib', ['lib*.ml{,i}'])
nexe = ocaml.NativeExecutable('exe.native', ['exe.ml'], libs=[nlib])

lib = ocaml.Library('lib', ['lib*.ml{,i}'])
exe = ocaml.Executable('exe.native', ['exe.ml'], libs=[lib])

def build():
    bexe.build()
    nexe.build()
    exe.build()
