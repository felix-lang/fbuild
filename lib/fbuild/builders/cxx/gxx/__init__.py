from functools import partial

from fbuild import Record
import fbuild.builders
from ...c import MissingHeader
from ...c import gcc

# -----------------------------------------------------------------------------

def config_gxx(env, exe=None, default_exes=['g++', 'c++']):
    exe = exe or fbuild.builders.find_program(default_exes)

    if not exe:
        raise ConfigFailed('cannot find g++')

    gxx = gcc.Gcc(exe)

    if not gxx.check_flags([]):
        raise ConfigFailed('g++ failed to compile an exe')

    return gxx

def make_compiler(*args, make_gcc=config_gxx, **kwargs):
    return gcc.make_compiler(make_gcc=make_gcc, *args, **kwargs)

def make_linker(*args, make_gcc=config_gxx, **kwargs):
    return gcc.make_linker(make_gcc=make_gcc, *args, **kwargs)

# -----------------------------------------------------------------------------

def config_static(*args, src_suffix='.cc', **kwargs):
    return gcc.config_static(src_suffix=src_suffix, *args, **kwargs)

def config_shared(*args, src_suffix='.cc', **kwargs):
    return gcc.config_shared(src_suffix=src_suffix, *args, **kwargs)

def config(*args,
        config_gxx=config_gxx,
        config_static=config_static,
        config_shared=config_shared,
        **kwargs):
    return gcc.config(
        config_gcc=config_gxx,
        config_static=config_static,
        config_shared=config_shared,
        *args, **kwargs)

# -----------------------------------------------------------------------------

def config_ext_hash_map(env, builder):
    if not builder.check_header_exists('ext/hash_map'):
        raise MissingHeader('ext/hash_map')

    hash_map = builder.check_compile('''
        #include <ext/hash_map>
        using namespace __gnu_cxx;

        int main(int argc,char** argv) {
            return 0;
        }
    ''', 'checking if gnu hash_map is supported')

    return Record(hash_map=hash_map)

def config_ext_headers(env, builder):
    return Record(
        hash_map=env.config(config_ext_hash_map, builder),
    )

def config_extensions(env, builder):
    return Record(
        headers=env.config(config_ext_headers, builder),
    )
