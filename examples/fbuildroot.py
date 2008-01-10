import os
from optparse import make_option

# -----------------------------------------------------------------------------

cmdline_options = [
    make_option('--ocamlc'),
    make_option('--ocamlopt'),
    make_option('--ocamllex'),
    make_option('--ocamlyacc'),
    make_option('--host-cc'),
    make_option('--host-cxx'),
    make_option('--target-cc'),
    make_option('--target-cxx'),
]

# -----------------------------------------------------------------------------

def config_c_compatible_builder(group, builder):
    #group.subconfigure('fbuild.builders.c.std.detect_std_types', builder)
    group.subconfigure('fbuild.builders.c.posix.config_posix_support', builder)
    #import fbuild.builders.c.posix
    #fbuild.builders.c.posix.config_posix_support(builder)

def config_c_builder(system, group, *args, **kwargs):
    c = group.make_config_subgroup('c')
    static = c.configure('static', 'fbuild.builders.c.config_static', system, *args, **kwargs)
    config_c_compatible_builder(c, static)

    shared = c.configure('shared', 'fbuild.builders.c.config_shared', system, *args, **kwargs)
    config_c_compatible_builder(c, shared)

def config_cxx_builder(sstem, group, *args, **kwargs):
    cxx = group.make_config_subgroup('cxx')
    static = cxx.configure('static', 'fbuild.builders.cxx.config_static', system, *args, **kwargs)
    config_c_compatible_builder(cxx, static)

    shared = cxx.configure('shared', 'fbuild.builders.cxx.config_shared', system, *args, **kwargs)
    config_c_compatible_builder(cxx, shared)

# -----------------------------------------------------------------------------

def config_build(system, options):
    system.log(0, 'configuring build phase', color='green')
    group = system.make_config_subgroup('build')
    #config_c_builder(group, system, options, exe=options.build_cc)
    #config_cxx_builder(group, system, options, exe=options.build_cxx)

def config_host(system, options):
    system.log(0, 'configuring host phase', color='green')
    group = system.make_config_subgroup('host')
    config_c_builder(system, group, options, exe=options.host_cc)
    #config_cxx_builder(system, group, options, system, exe=options.host_cxx)

    group.configure('ocaml', 'fbuild.builders.ocaml.config',
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc,
    )

def config_target(system, options):
    system.log(0, 'configuring target phase', color='green')
    group = system.make_config_subgroup('target')
    config_c_builder(system, group, options, exe=options.target_cc)
    #config_cxx_builder(system, group, options, exe=options.target_cxx)

# -----------------------------------------------------------------------------

def configure(system, options):
    config_build(system, options)
    config_host(system, options)
    config_target(system, options)

def build(system, options):
    static = system.config['target']['c']['static']
    objects = static.compile(['foo.c'])
    exe = static.link_exe('foo', objects)
    system.execute([os.path.join('.', exe)], ('running', exe))
