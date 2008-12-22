from optparse import make_option
import pprint

import fbuild.db
import fbuild.builders.c.c99 as c99
import fbuild.builders.c.guess
import fbuild.builders.cxx.guess
import fbuild.builders.platform
import fbuild.builders.ocaml

from fbuild import ConfigFailed, execute, logger
from fbuild.path import Path
from fbuild.record import Record

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

def run_tests(tests, *args, **kwargs):
    for test in tests:
        fbuild.functools.call(test, *args, **kwargs)

def run_optional_tests(tests, *args, **kwargs):
    for test in tests:
        try:
            fbuild.functools.call(test, *args, **kwargs)
        except ConfigFailed:
            pass

def make_c_builder(**kwargs):
    c = fbuild.builders.c.guess.config(**kwargs)

    run_tests(c_tests, c.static)
    run_optional_tests(c_optional_tests, c.static)
    run_optional_tests(c_optional_shared_tests, c.static)

    return c

def make_cxx_builder(**kwargs):
    cxx = fbuild.builders.cxx.guess.config(**kwargs)

    run_tests(cxx_tests, cxx.static)
    run_optional_tests(c_optional_tests, cxx.static)
    run_optional_tests(c_optional_shared_tests, cxx.static)
    run_optional_tests(cxx_optional_tests, cxx.static)

    return cxx

@fbuild.db.caches
def config_build(*, platform, cc, cxx):
    logger.log('configuring build phase', color='cyan')

    return Record(
        platform=fbuild.builders.platform.config(platform),
        c=make_c_builder(exe=cc),
        cxx=make_cxx_builder(exe=cxx),
    )

@fbuild.db.caches
def config_host(build, *,
        platform, cc, cxx, ocamlc, ocamlopt, ocamllex, ocamlyacc):
    logger.log('configuring host phase', color='cyan')

    platform = fbuild.builders.platform.config(platform)

    if platform == build.platform:
        logger.log("using build's c and cxx compiler")
        phase = build
    else:
        phase = Record(
            platform=platform,
            c=make_c_builder(exe=cc),
            cxx=make_cxx_builder(exe=cxx))

    phase.ocaml = fbuild.builders.ocaml.config(
        ocamlc=ocamlc,
        ocamlopt=ocamlopt,
        ocamllex=ocamllex,
        ocamlyacc=ocamlyacc)

    return phase

@fbuild.db.caches
def config_target(host, *, platform, cc, cxx):
    logger.log('configuring target phase', color='cyan')

    platform = fbuild.builders.platform.config(platform)

    if platform == host.platform:
        logger.log("using host's c and cxx compiler")
        phase = host
    else:
        phase = Record(
            platform=platform,
            c=make_c_builder(exe=cc),
            cxx=make_cxx_builder(exe=cxx))

    return phase

# -----------------------------------------------------------------------------

def build():
    from fbuild import options

    # configure the phases
    build = config_build(
        platform=options.build_platform,
        cc=options.build_cc,
        cxx=options.build_cxx)

    host = config_host(build,
        platform=options.host_platform,
        cc=options.host_cc,
        cxx=options.host_cxx,
        ocamlc=options.ocamlc,
        ocamlopt=options.ocamlopt,
        ocamllex=options.ocamllex,
        ocamlyacc=options.ocamlyacc)

    target = config_target(host,
        platform=options.target_platform,
        cc=options.target_cc,
        cxx=options.target_cxx)

    pprint.pprint(c99.type_aliases_stdint_h(target.c.static))

    for lang in 'c', 'cxx':
        for mode in 'static', 'shared':
            builder = target[lang][mode]

            d = Path(lang, mode)
            try:
                d.rmtree()
            except OSError:
                pass

            d.makedirs()
            Path.copy('foo.c', d)
            Path.copy('bar.c', d)

            obj = builder.compile(d / 'bar.c')
            lib = builder.link_lib(d / 'bar', [obj])

            obj = builder.compile(d / 'foo.c')
            exe = builder.link_exe(d / 'foo', [obj], libs=[lib])
            execute([exe], 'running', exe)
