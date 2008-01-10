from fbuild import configure

ocaml_builder = configure('fbuild.builders.ocaml.config', name='host')

c_static_builder = configure('fbuild.builders.c.config_static', name='host')
c_shared_builder = configure('fbuild.builders.c.config_shared', name='host')

cxx_static_builder = configure('fbuild.builders.cxx.config_static', name='host')
cxx_shared_builder = configure('fbuild.builders.cxx.config_shared', name='host')
