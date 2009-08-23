import fbuild.builders.ocaml
from fbuild.path import Path

def build(ctx):
    ocaml = fbuild.builders.ocaml.Ocaml(ctx)

    libb = ocaml.ocamlc.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.ocamlc.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.ocamlc.build_exe('exe.byte', ['exe.ml'], libs=[libb, liba])

    ctx.logger.log(' * running %s:' % exe)
    ctx.execute([exe])

    libb = ocaml.ocamlopt.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.ocamlopt.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.ocamlopt.build_exe('exe.native', ['exe.ml'], libs=[libb, liba])

    ctx.logger.log(' * running %s:' % exe)
    ctx.execute([exe])

    # We can also build bytecode and native libraries at the same time.
    libb = ocaml.build_lib('libb', Path.glob('b*.ml{,i}'))
    liba = ocaml.build_lib('liba', Path.glob('a*.ml{,i}'), libs=[libb])
    exe  = ocaml.build_exe('exe', ['exe.ml'], libs=[libb, liba]).bytecode
