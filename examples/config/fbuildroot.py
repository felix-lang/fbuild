import functools

import fbuild
import fbuild.builders.c
import fbuild.builders.cxx
import fbuild.config as config
from fbuild.functools import import_module

# ------------------------------------------------------------------------------

def test_field(ctx, test, field):
    if getattr(test, field.__name__):
        return True
    else:
        ctx.logger.check('%r failed test' % str(test.builder),
            '%s.%s.%s' % (
                test.__class__.__module__,
                test.__class__.__name__,
                field.__name__),
            color='yellow')

        try:
            src = field.method.test or field.method.format_test(
                getattr(test, 'header', None))
        except AttributeError as e:
            pass
        else:
            ctx.logger.log(src, verbose=1)

        return False

def test_test(ctx, test):
    passed = 0
    total = 0

    for result in ctx.scheduler.map(
            functools.partial(test_field, ctx, test),
            (f for n, f in test.fields())):
        total += 1
        if result:
            passed += 1

    return passed, total

def test_module(ctx, builder, module):
    tests = []
    for name in dir(module):
        test = getattr(module, name)
        if isinstance(test, type) and issubclass(test, config.Test):
            tests.append(test(builder))

    passed = 0
    total = 0
    for p, t in ctx.scheduler.map(functools.partial(test_test, ctx), tests):
        passed += p
        total += t
    return passed, total

def build(ctx):
    c_static = fbuild.builders.c.guess_static(ctx)
    c_shared = fbuild.builders.c.guess_shared(ctx)
    cxx_static = fbuild.builders.cxx.guess_static(ctx, platform_options=[
        ({'windows'}, {'flags': ['/EHsc']}),
    ])
    cxx_shared = fbuild.builders.cxx.guess_shared(ctx, platform_options=[
        ({'windows'}, {'flags': ['/EHsc']}),
    ])
    passed = 0
    total = 0

    # c tests
    for builder in c_static, c_shared, cxx_static, cxx_shared:
        for module in (
                import_module('fbuild.config.c.bsd'),
                import_module('fbuild.config.c.c90'),
                import_module('fbuild.config.c.c99'),
                import_module('fbuild.config.c.darwin'),
                import_module('fbuild.config.c.ieeefp_h'),
                import_module('fbuild.config.c.linux'),
                import_module('fbuild.config.c.malloc'),
                import_module('fbuild.config.c.posix'),
                import_module('fbuild.config.c.posix01'),
                import_module('fbuild.config.c.posix04'),
                import_module('fbuild.config.c.stdlib'),
                import_module('fbuild.config.c.win32')):
            p, t = test_module(ctx, builder, module)
            passed += p
            total += t

    # c++ tests
    for builder in cxx_static, cxx_shared:
        for module in (
                import_module('fbuild.config.cxx.cxx03'),
                import_module('fbuild.config.cxx.cmath'),
                import_module('fbuild.config.cxx.iterator'),
                import_module('fbuild.config.cxx.gtest'),
                import_module('fbuild.config.cxx.gnu')):
            p, t = test_module(ctx, builder, module)
            passed += p
            total += t

    ctx.logger.log('%d/%d tests' % (passed, total))
