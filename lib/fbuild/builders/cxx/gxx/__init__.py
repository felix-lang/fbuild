from functools import partial

import fbuild.builders
from ...c import gcc as Gcc

# -----------------------------------------------------------------------------

def make_gxx(system, exe=None, default_exes=['g++', 'c++']):
    exe = exe or fbuild.builders.find_program(system, default_exes)

    if not exe:
        raise ConfigFailed('cannot find g++')

    gxx = Gcc.Gcc(system, exe)

    if not gxx.check_flags([]):
        raise ConfigFailed('g++ failed to compile an exe')

    return gxx

# -----------------------------------------------------------------------------

def config(conf, exe, *args, **kwargs):
    from ... import ar

    return conf.subconfigure('cxx', Gcc.config_builder,
        make_gxx(conf.system, exe),
        partial(ar.config, conf),
        *args,
        **kwargs)

# -----------------------------------------------------------------------------

def config_ext_hash_map(conf, builder):
    conf.configure('ext.hash_map', builder.check_header_exists, 'ext/hash_map')

def config_extensions(conf, builder):
    config_ext_hash_map(conf, builder)
