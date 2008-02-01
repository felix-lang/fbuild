import os
import shutil
from optparse import make_option

# -----------------------------------------------------------------------------

def pre_options(parser):
    group = parser.add_option_group('config options')
    group.add_options([
        make_option('--ocamlc'),
        make_option('--ocamlopt'),
        make_option('--ocamllex'),
        make_option('--ocamlyacc'),
        make_option('--build-cc'),
        make_option('--build-cxx'),
        make_option('--host-cc'),
        make_option('--host-cxx'),
        make_option('--target-cc'),
        make_option('--target-cxx'),
    ])

# -----------------------------------------------------------------------------

c_tests = [
    'fbuild.builders.c.std.config',
    'fbuild.builders.c.config_little_endian',
]

c_optional_tests = [
    'fbuild.builders.c.c99.config',
    'fbuild.builders.c.math.config',
    'fbuild.builders.c.posix.config',
    'fbuild.builders.c.bsd.config',
    'fbuild.builders.c.linux.config',
    'fbuild.builders.c.solaris.config',
    'fbuild.builders.c.win32.config',
    'fbuild.builders.c.gcc.config_extensions',
]

cxx_tests = []

cxx_optional_tests = [
    'fbuild.builders.cxx.cmath.config',
    'fbuild.builders.cxx.gxx.config_extensions',
]


def make_c_builder(conf, **kwargs):
    from fbuild.builders.c.gcc.darwin import config
    return config(conf,
        tests=c_tests,
        optional_tests=c_optional_tests,
        **kwargs)


def make_cxx_builder(conf, **kwargs):
    from fbuild.builders.cxx.gxx.darwin import config
    return config(conf,
        tests=c_tests + cxx_tests,
        optional_tests=c_optional_tests + cxx_optional_tests,
        **kwargs)


def config_build(conf, options, model):
    conf.log('configuring build phase', color='green')
    conf['model'] = model
    make_c_builder(conf, exe=options.build_cc)
    make_cxx_builder(conf, exe=options.build_cxx)


def config_host(conf, options, model, build):
    conf.log('configuring host phase')
    conf['model'] = model

    if model == build['model']:
        conf.log("using build's c and cxx compiler")
        conf['c']   = build['c']
        conf['cxx'] = build['cxx']
    else:
        make_c_builder(conf, exe=options.host_cc)
        make_cxx_builder(conf, exe=options.host_cxx)

    conf.configure('ocaml', 'fbuild.builders.ocaml.config',
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc,
    )


def config_target(conf, options, model, host):
    conf.log('configuring target phase')
    conf['model'] = model

    if model == host['model']:
        conf.log("using host's c and cxx compiler")
        conf['c']   = host['c']
        conf['cxx'] = host['cxx']
    else:
        make_c_builder(conf, exe=options.target_cc)
        make_cxx_builder(conf, exe=options.target_cxx)

# -----------------------------------------------------------------------------

def configure(system, options):
    model = None

    build  = system.subconfigure('build',  config_build,  options, model)
    host   = system.subconfigure('host',   config_host,   options, model, build)
    target = system.subconfigure('target', config_target, options, model, host)


def build(system, options):
    conf = system.config['target']
    import fbuild.builders.c.c99 as c99
    import pprint
    pprint.pprint(c99.type_aliases_stdint_h(conf.c))

    for lang in 'c', 'cxx':
        for mode in 'static', 'shared':
            builder = conf[lang][mode]

            d = os.path.join(lang, mode)
            try:
                shutil.rmtree(d)
            except OSError:
                pass

            os.makedirs(d)
            shutil.copy('foo.c', d)
            shutil.copy('bar.c', d)

            objects = builder.compile([(d, 'bar.c')])
            lib = builder.link_lib((d, 'bar'), objects)

            objects = builder.compile([(d, 'foo.c')])
            exe = builder.link_exe((d, 'foo'), objects, libs=[lib])
            system.execute([exe], 'running', exe)
