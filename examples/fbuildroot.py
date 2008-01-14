import os
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
    'fbuild.builders.c.std.detect_std_types',
    'fbuild.builders.c.posix.config_posix_support',
]

def config_build(config, options, model):
    config.log(0, 'configuring build phase', color='green')
    config['model'] = model

    config.subconfigure('c', 'fbuild.builders.c.gcc.darwin.config',
        exe=options.build_cc,
        tests=c_tests,
    )

    config.subconfigure('cxx', 'fbuild.builders.cxx.gxx.darwin.config',
        exe=options.build_cxx,
        tests=c_tests,
    )


def config_host(config, options, model, build):
    config.log(0, 'configuring host phase')
    config['model'] = model

    if model == build['model']:
        config.log(0, "using build's c and cxx compiler")
        config['c']   = build['c']
        config['cxx'] = build['cxx']
    else:
        config.subconfigure('c', 'fbuild.builders.c.gcc.darwin.config',
            exe=options.build_cc,
            tests=c_tests,
        )

        config.subconfigure('cxx', 'fbuild.builders.cxx.gxx.darwin.config',
            exe=options.build_cxx,
            tests=c_tests,
        )

    config.configure('ocaml', 'fbuild.builders.ocaml.config',
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc,
    )


def config_target(config, options, model, host):
    config.log(0, 'configuring target phase')
    config['model'] = model

    if model == host['model']:
        config.log(0, "using host's c and cxx compiler")
        config['c']   = host['c']
        config['cxx'] = host['cxx']
    else:
        config.subconfigure('c', 'fbuild.builders.c.gcc.darwin.config',
            exe=options.build_cc,
            tests=c_tests,
        )

        config.subconfigure('cxx', 'fbuild.builders.cxx.gxx.darwin.config',
            exe=options.build_cxx,
            tests=c_tests,
        )

# -----------------------------------------------------------------------------

def configure(system, options):
    model = None

    build  = system.subconfigure('build',  config_build,  options, model)
    host   = system.subconfigure('host',   config_host,   options, model, build)
    target = system.subconfigure('target', config_target, options, model, host)


def build(system, options):
    import shutil

    for lang in 'c', 'cxx':
        for mode in 'static', 'shared':
            builder = system.config['build'][lang][mode]['builder']

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
            exe = builder.link_exe(os.path.join(d, 'foo'), objects, libs=[lib])
            system.execute([exe], ('running', exe))
