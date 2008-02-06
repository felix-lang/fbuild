import os
import shutil
from optparse import make_option
import pprint

import fbuild.builders.platform as platform
import fbuild.builders.c.c99 as c99

# -----------------------------------------------------------------------------

def pre_options(parser):
    group = parser.add_option_group('config options')
    group.add_options((
        make_option('--build-platform'),
        make_option('--build-cc'),
        make_option('--build-cxx'),
        make_option('--host-platform'),
        make_option('--host-cc'),
        make_option('--host-cxx'),
        make_option('--target-platform'),
        make_option('--target-cc'),
        make_option('--target-cxx'),
        make_option('--ocamlc'),
        make_option('--ocamlopt'),
        make_option('--ocamllex'),
        make_option('--ocamlyacc'),
    ))

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
    from fbuild.builders.c.guess import config
    c = config(conf, **kwargs)

    c.run_tests(c_tests)
    c.run_optional_tests(c_optional_tests)

def make_cxx_builder(conf, **kwargs):
    from fbuild.builders.cxx.guess import config
    cxx = config(conf, **kwargs)

    cxx.run_tests(c_tests)
    cxx.run_tests(cxx_tests)
    cxx.run_optional_tests(c_optional_tests)
    cxx.run_optional_tests(cxx_optional_tests)

def config_build(conf, options):
    conf.log('configuring build phase', color='green')

    platform.config(conf, options.host_platform)
    make_c_builder(conf, exe=options.build_cc)
    make_cxx_builder(conf, exe=options.build_cxx)

def config_host(conf, options, build):
    conf.log('configuring host phase')

    platform.config(conf, options.host_platform)

    if conf.platform == build.platform:
        conf.log("using build's c and cxx compiler")
        conf.c   = build.c
        conf.cxx = build.cxx
    else:
        make_c_builder(conf, exe=options.host_cc)
        make_cxx_builder(conf, exe=options.host_cxx)

    conf.configure('ocaml', 'fbuild.builders.ocaml.config',
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc,
    )

def config_target(conf, options, host):
    conf.log('configuring target phase')

    platform.config(conf, options.target_platform)

    if conf.platform == host.platform:
        conf.log("using host's c and cxx compiler")
        conf.c   = host.c
        conf.cxx = host.cxx
    else:
        make_c_builder(conf, exe=options.target_cc)
        make_cxx_builder(conf, exe=options.target_cxx)

# -----------------------------------------------------------------------------

def configure(system, options):
    conf = system.config
    config_build(conf.config_group('build'), options)
    config_host(conf.config_group('host'), options, conf.build)
    config_target(conf.config_group('target'), options, conf.host)


def build(system, options):
    conf = system.config.target
    pprint.pprint(c99.type_aliases_stdint_h(conf.c))

    for lang in 'c', 'cxx':
        for mode in 'static', 'shared':
            builder = getattr(getattr(conf, lang), mode)

            d = os.path.join(lang, mode)
            try:
                shutil.rmtree(d)
            except OSError:
                pass

            os.makedirs(d)
            shutil.copy('foo.c', d)
            shutil.copy('bar.c', d)

            obj = builder.compile((d, 'bar.c'))
            lib = builder.link_lib((d, 'bar'), [obj])

            obj = builder.compile((d, 'foo.c'))
            exe = builder.link_exe((d, 'foo'), [obj], libs=[lib])
            system.execute([exe], 'running', exe)
