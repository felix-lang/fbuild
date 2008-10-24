import fbuild

def build():
    ocaml = fbuild.env.cache('fbuild.builders.ocaml.config_ocaml')

    lib = ocaml.bytecode.build_lib('lib', ['lib*.ml{,i}'])
    exe = ocaml.bytecode.build_exe('exe.byte', ['exe.ml'], libs=[lib])

    lib = ocaml.native.build_lib('lib', ['lib*.ml{,i}'])
    exe = ocaml.native.build_exe('exe.native', ['exe.ml'], libs=[lib])

    lib = ocaml.native.build_lib('lib', ['lib*.ml{,i}'])
    exe = ocaml.native.build_exe('exe', ['exe.ml'], libs=[lib])
