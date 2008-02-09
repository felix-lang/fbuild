from functools import partial

import fbuild.builders
from ...c import MissingHeader
from ...c import gcc

# -----------------------------------------------------------------------------

def config_gxx(conf, exe=None, default_exes=['g++', 'c++']):
    try:
        return conf.gxx
    except AttributeError:
        pass

    exe = exe or fbuild.builders.find_program(default_exes)

    if not exe:
        raise ConfigFailed('cannot find g++')

    gxx = conf['gxx'] = gcc.Gcc(exe)

    if not gxx.check_flags([]):
        raise ConfigFailed('g++ failed to compile an exe')

    return gxx

def make_compiler(*args, make_gcc=config_gxx, **kwargs):
    return gcc.make_compiler(make_gcc=make_gcc, *args, **kwargs)

def make_linker(*args, make_gcc=config_gxx, **kwargs):
    return gcc.make_linker(make_gcc=make_gcc, *args, **kwargs)

# -----------------------------------------------------------------------------

def config_static(conf, *args,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c'],
        src_suffix='.cc',
        **kwargs):
    from ... import ar

    conf.setdefault('cxx', {})['static'] = gcc.make_static(conf,
        partial(make_compiler, flags=compile_flags),
        ar.config,
        make_linker,
        src_suffix=src_suffix,
        *args, **kwargs)

def config_shared(conf, *args,
        make_compiler=make_compiler,
        make_linker=make_linker,
        compile_flags=['-c', '-fPIC'],
        lib_link_flags=['-shared'],
        src_suffix='.cc',
        **kwargs):
    conf.setdefault('cxx', {})['shared'] = gcc.make_shared(conf,
        partial(make_compiler, flags=compile_flags),
        partial(make_linker, flags=lib_link_flags),
        make_linker,
        src_suffix=src_suffix,
        *args, **kwargs)

def config(conf, exe, *args,
        config_gxx=config_gxx,
        config_static=config_static,
        config_shared=config_shared,
        **kwargs):
    config_gxx(conf, exe)
    config_static(conf, *args, **kwargs)
    config_shared(conf, *args, **kwargs)

    return conf['cxx']

# -----------------------------------------------------------------------------

def config_ext_hash_map(conf):
    if not conf['static'].check_header_exists('ext/hash_map'):
        raise MissingHeader('ext/hash_map')

    # FIXME: just make a hash_map stub until we write a test for it
    conf.setdefault('ext', {}).setdefault('hash_map', {})

def config_extensions(conf):
    config_ext_hash_map(conf)
