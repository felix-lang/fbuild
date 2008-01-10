from fbuild.system import configure

c_static_builder = configure('fbuild.builders.c.config_static', name='target')
c_shared_builder = configure('fbuild.builders.c.config_shared', name='target')

cxx_static_builder = configure('fbuild.builders.cxx.config_static', name='target')
cxx_shared_builder = configure('fbuild.builders.cxx.config_shared', name='target')
