import fbuild.system
import fbuild.conf.c.gcc as gcc

# -----------------------------------------------------------------------------

#@fbuild.system.system_cache
def config_link_dynamiclib(system, *args, **kwargs):
    return gcc.GccLinker([gcc.find_gcc_exe(system), '-dynamiclib'],
        *args, **kwargs)


#@fbuild.system.system_cache
def static(system):
    return gcc.static(system)


#@fbuild.system.system_cache
def shared(system):
    return gcc.config_builder(system,
        gcc.config_compile_shared, config_link_dynamiclib, gcc.config_link_exe,
        '.os', 'lib', '.dylib', '')
