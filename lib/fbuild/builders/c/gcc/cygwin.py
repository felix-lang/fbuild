import fbuild.system
import fbuild.conf.c.gcc as gcc

# -----------------------------------------------------------------------------

def static(system):
    return gcc.static(system, '.obj', '', '.lib', '.exe')


def shared(system):
    return gcc.config_builder(system,
        gcc.config_compile_shared, config_link_dynamiclib, gcc.config_link_exe,
        '.obj', '', '.dll', '.exe')
