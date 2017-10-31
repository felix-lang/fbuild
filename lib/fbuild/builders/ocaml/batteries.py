import fbuild.builders.ocaml.ocamlfind as ocamlfind

# ------------------------------------------------------------------------------

class Ocamldep(ocamlfind.Ocamldep):
    def __init__(self, *args, packages=[], **kwargs):
        super().__init__(*args, packages=packages+['batteries'], **kwargs)

class Ocamlc(ocamlfind.Ocamlc):
    def __init__(self, *args,
            make_ocamldep=Ocamldep,
            packages=[],
            **kwargs):
        super().__init__(*args,
            make_ocamldep=make_ocamldep,
            packages=packages+['batteries'],
            **kwargs)

class Ocamlcp(ocamlfind.Ocamlcp):
    def __init__(self, *args,
            make_ocamldep=Ocamldep,
            packages=[],
            **kwargs):
        super().__init__(*args,
            make_ocamldep=make_ocamldep,
            packages=packages+['batteries'],
            **kwargs)

class Ocamlopt(ocamlfind.Ocamlopt):
    def __init__(self, *args,
            make_ocamldep=Ocamldep,
            make_ocamlc=Ocamlc,
            packages=[],
            **kwargs):
        super().__init__(*args,
            make_ocamldep=make_ocamldep,
            make_ocamlc=make_ocamlc,
            packages=packages+['batteries'],
            **kwargs)

class Ocaml(ocamlfind.Ocaml):
    def __init__(self, *args,
            make_ocamldep=Ocamldep,
            make_ocamlc=Ocamlc,
            make_ocamlcp=Ocamlcp,
            make_ocamlopt=Ocamlopt,
            **kwargs):
        super().__init__(*args,
            make_ocamldep=make_ocamldep,
            make_ocamlc=make_ocamlc,
            make_ocamlcp=make_ocamlcp,
            make_ocamlopt=make_ocamlopt,
            **kwargs)
