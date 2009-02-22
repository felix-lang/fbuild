from optparse import make_option
import pprint

import fbuild.builders.c
import fbuild.config.c as c
import fbuild.config.c.c99 as c99
from fbuild import execute, logger
from fbuild.functools import call
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

def make_c_builder(**kwargs):
    static = call('fbuild.builders.c.guess_static', **kwargs)
    shared = call('fbuild.builders.c.guess_shared', **kwargs)

    return Record(
        static=static,
        shared=shared)

def make_cxx_builder(**kwargs):
    static = call('fbuild.builders.cxx.guess_static', **kwargs)
    shared = call('fbuild.builders.cxx.guess_shared', **kwargs)

    return Record(
        static=static,
        shared=shared)

@fbuild.db.caches
def config_build(*, platform, cc, cxx):
    logger.log('configuring build phase', color='cyan')

    return Record(
        platform=call('fbuild.builders.platform.platform', platform),
        c=make_c_builder(exe=cc),
        cxx=make_cxx_builder(exe=cxx),
    )

@fbuild.db.caches
def config_host(build, *,
        platform, cc, cxx, ocamlc, ocamlopt, ocamllex, ocamlyacc):
    logger.log('configuring host phase', color='cyan')

    platform = call('fbuild.builders.platform.platform', platform)

    if platform == build.platform:
        logger.log("using build's c and cxx compiler")
        phase = build
    else:
        phase = Record(
            platform=platform,
            c=make_c_builder(exe=cc),
            cxx=make_cxx_builder(exe=cxx))

    phase.ocaml = call('fbuild.builders.ocaml.Ocaml',
        ocamlc=ocamlc,
        ocamlopt=ocamlopt,
    )
    phase.ocamllex = call('fbuild.builders.ocaml.Ocamllex', ocamllex)
    phase.ocamlyacc = call('fbuild.builders.ocaml.Ocamlyacc', ocamlyacc)

    return phase

@fbuild.db.caches
def config_target(host, *, platform, cc, cxx):
    logger.log('configuring target phase', color='cyan')

    platform = call('fbuild.builders.platform.platform', platform)

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

    types = c99.types(target.c.static)
    stdint_h = c99.stdint_h(target.c.static)

    stdint_types = {'char': types.structural_alias(types.char)}
    for name, field in stdint_h.fields():
        t = getattr(stdint_h, name)
        if isinstance(t, c.IntType):
            stdint_types[field.method.name] = types.structural_alias(t)

    pprint.pprint(stdint_types)

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
            lib = builder.link_lib(d / 'bar', [obj], exports=['bar'])

            obj = builder.compile(d / 'foo.c')
            exe = builder.link_exe(d / 'foo', [obj], libs=[lib])
            execute([exe], 'running', exe)
