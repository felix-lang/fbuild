from optparse import make_option
import pprint

import fbuild
from fbuild import ConfigFailed, execute, logger
from fbuild.path import Path
from fbuild.record import Record
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
    'fbuild.builders.c.bsd.config',
    'fbuild.builders.c.linux.config',
    'fbuild.builders.c.solaris.config',
    'fbuild.builders.c.win32.config',
    'fbuild.builders.c.gcc.config_extensions',
    'fbuild.builders.c.openmp.config',
]

c_optional_shared_tests = [
    'fbuild.builders.c.posix.config',
]

cxx_tests = [
    'fbuild.builders.cxx.std.config',
    'fbuild.builders.c.config_little_endian',
]

cxx_optional_tests = [
    'fbuild.builders.cxx.cmath.config',
    'fbuild.builders.cxx.gxx.config_extensions',
]

def run_tests(env, tests, *args, **kwargs):
    for test in tests:
        env.config(test, *args, **kwargs)

def run_optional_tests(env, tests, *args, **kwargs):
    for test in tests:
        try:
            env.config(test, *args, **kwargs)
        except ConfigFailed:
            pass

def make_c_builder(env, **kwargs):
    c = env.config('fbuild.builders.c.guess.config', **kwargs)

    run_tests(env, c_tests, c.static)
    run_optional_tests(env, c_optional_tests, c.static)
    run_optional_tests(env, c_optional_shared_tests, c.static)

    return c

def make_cxx_builder(env, **kwargs):
    cxx = env.config('fbuild.builders.cxx.guess.config', **kwargs)

    run_tests(env, cxx_tests, cxx.static)
    run_optional_tests(env, c_optional_tests, cxx.static)
    run_optional_tests(env, c_optional_shared_tests, cxx.static)
    run_optional_tests(env, cxx_optional_tests, cxx.static)

    return cxx

def config_build(env, *, platform, cc, cxx):
    logger.log('configuring build phase', color='cyan')

    return Record(
        platform=env.config('fbuild.builders.platform.config', platform),
        c=make_c_builder(env, exe=cc),
        cxx=make_cxx_builder(env, exe=cxx),
    )

def config_host(env, build, *,
        platform, cc, cxx, ocamlc, ocamlopt, ocamllex, ocamlyacc):
    logger.log('configuring host phase', color='cyan')

    platform = env.config('fbuild.builders.platform.config', platform)

    if platform == build.platform:
        logger.log("using build's c and cxx compiler")
        phase = build
    else:
        phase = Record(
            platform=platform,
            c=make_c_builder(env, exe=cc),
            cxx=make_cxx_builder(env, exe=cxx))

    phase.ocaml = env.config('fbuild.builders.ocaml.config',
        ocamlc=ocamlc,
        ocamlopt=ocamlopt,
        ocamllex=ocamllex,
        ocamlyacc=ocamlyacc)

    return phase

def config_target(env, host, *, platform, cc, cxx):
    logger.log('configuring target phase', color='cyan')

    platform = env.config('fbuild.builders.platform.config', platform)

    if platform == host.platform:
        logger.log("using host's c and cxx compiler")
        phase = host
    else:
        phase = Record(
            platform=platform,
            c=make_c_builder(env, exe=cc),
            cxx=make_cxx_builder(env, exe=cxx))

    return phase

# -----------------------------------------------------------------------------

def build(env):
    from fbuild import options

    # configure the phases
    build = env.config(config_build,
        platform=options.build_platform,
        cc=options.build_cc,
        cxx=options.build_cxx)

    host = env.config(config_host, build,
        platform=options.host_platform,
        cc=options.host_cc,
        cxx=options.host_cxx,
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc)

    target = env.config(config_target, host,
        platform=options.target_platform,
        cc=options.target_cc,
        cxx=options.target_cxx)

    pprint.pprint(c99.type_aliases_stdint_h(env, target.c.static))

    for lang in 'c', 'cxx':
        for mode in 'static', 'shared':
            builder = target[lang][mode]

            d = Path(lang, mode)
            try:
                d.rmtree()
            except OSError:
                pass

            d.make_dirs()
            Path.copy('foo.c', d)
            Path.copy('bar.c', d)

            obj = builder.compile(d / 'bar.c')
            lib = builder.link_lib(d / 'bar', [obj])

            obj = builder.compile(d / 'foo.c')
            exe = builder.link_exe(d / 'foo', [obj], libs=[lib])
            execute([exe], 'running', exe)
