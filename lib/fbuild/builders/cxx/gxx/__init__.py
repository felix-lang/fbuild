from fbuild import ConfigFailed, env
from fbuild.builders import find_program
from fbuild.builders.c import MissingHeader, gcc
from fbuild.record import Record

# -----------------------------------------------------------------------------

def config_gxx(exe=None, default_exes=['g++', 'c++']):
    exe = exe or find_program(default_exes)

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

def config_static(*args, config_gxx=config_gxx, src_suffix='.cc', **kwargs):
    return gcc.config_static(
        config_gcc=config_gxx,
        src_suffix=src_suffix,
        *args, **kwargs)

def config_shared(*args, config_gxx=config_gxx, src_suffix='.cc', **kwargs):
    return gcc.config_shared(
        config_gcc=config_gxx,
        src_suffix=src_suffix,
        *args, **kwargs)

# -----------------------------------------------------------------------------

def config_ext_hash_map(builder):
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

def config_ext_headers(builder):
    return Record(
        hash_map=env.cache(config_ext_hash_map, builder),
    )

def config_extensions(builder):
    return Record(
        headers=env.cache(config_ext_headers, builder),
    )
