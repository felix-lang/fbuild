import fbuild.builders.ocaml.batteries
from fbuild.path import Path

def build(ctx):
    ocaml = fbuild.builders.ocaml.batteries.Ocaml(ctx)

    lib = ocaml.ocamlc.build_lib('lib', Path.glob('lib*.ml{,i}'),
        packages=['ppx_sexp_conv', 'ppx_deriving'])
    print('here', lib)
    exe = ocaml.ocamlc.build_exe('exe.byte', ['exe.ml'], libs=[lib], packages=['sexplib'])

    ctx.logger.log(' * running %s:' % exe)
    ctx.execute([exe])

    lib = ocaml.ocamlopt.build_lib('lib', Path.glob('lib*.ml{,i}'),
        packages=['ppx_sexp_conv', 'ppx_deriving'])
    exe = ocaml.ocamlopt.build_exe('exe.byte', ['exe.ml'], libs=[lib], packages=['sexplib'])

    ctx.logger.log(' * running %s:' % exe)
    ctx.execute([exe])

    # We can also build bytecode and native libraries at the same time.
    lib = ocaml.build_lib('lib', Path.glob('lib*.ml{,i}'),
        packages=['ppx_sexp_conv', 'ppx_deriving'])
    exe = ocaml.build_exe('exe', ['exe.ml'], libs=[lib], packages=['sexplib']).bytecode
