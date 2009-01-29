import fbuild
import fbuild.builders
import fbuild.builders.c.gcc
import fbuild.db
import fbuild.record

# ------------------------------------------------------------------------------

def make_gxx(exe=None, default_exes=['g++', 'c++'], **kwargs):
    return fbuild.builders.c.gcc.make_gcc(exe, default_exes, **kwargs)

def make_compiler(*args, make_gcc=make_gxx, **kwargs):
    return fbuild.builders.gcc.make_compiler(*args, make_gcc=make_gcc, **kwargs)

def make_linker(*args, make_gcc=make_gxx, **kwargs):
    return fbuild.builders.gcc.make_linker(*args, make_gcc=make_gcc, **kwargs)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def static(*args, make_gxx=make_gxx, src_suffix='.cc', **kwargs):
    return fbuild.builders.c.gcc.static(*args,
        make_gcc=make_gxx,
        src_suffix=src_suffix,
        **kwargs)

@fbuild.db.caches
def shared(*args, make_gxx=make_gxx, src_suffix='.cc', **kwargs):
    return fbuild.builders.c.gcc.shared(*args,
        make_gcc=make_gxx,
        src_suffix=src_suffix,
        **kwargs)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def config_ext_hash_map(builder):
    if not builder.check_header_exists('ext/hash_map'):
        raise fbuild.builders.c.MissingHeader('ext/hash_map')

    hash_map = builder.check_compile('''
        #include <ext/hash_map>
        using namespace __gnu_cxx;

        int main(int argc,char** argv) {
            return 0;
        }
    ''', 'checking if gnu hash_map is supported')

    return fbuild.record.Record(hash_map=hash_map)

def config_ext_headers(builder):
    return fbuild.record.Record(
        hash_map=config_ext_hash_map(builder),
    )

def config_extensions(builder):
    return fbuild.record.Record(
        headers=config_ext_headers(builder),
    )
