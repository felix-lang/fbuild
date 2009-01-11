import fbuild.builders.ocaml
from fbuild.path import Path

def build():
    ocaml = fbuild.builders.ocaml.config_ocaml()

    libb = ocaml.bytecode.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.bytecode.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.bytecode.build_exe('exe.byte', ['exe.ml'], libs=[libb, liba])

    libb = ocaml.native.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.native.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.native.build_exe('exe.native', ['exe.ml'], libs=[libb, liba])

    libb = ocaml.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.build_exe('exe', ['exe.ml'], libs=[libb, liba]).bytecode
