import functools

import fbuild
import fbuild.builders.c
import fbuild.builders.cxx
import fbuild.config as config
import fbuild.config.c.c90 as c90
import fbuild.config.c.c99 as c99
import fbuild.config.c.posix04 as posix04
import fbuild.config.c.math_h as math_h
import fbuild.config.c.ieeefp_h as ieeefp_h
import fbuild.config.cxx.cxx03 as cxx03
import fbuild.config.cxx.cmath as cmath

# ------------------------------------------------------------------------------

def test_field(header, field):
    if getattr(header, field.__name__):
        return True
    else:
        fbuild.logger.check('failed test:',
            '%s.%s.%s' % (
                header.__class__.__module__,
                header.__class__.__name__,
                field.__name__),
            color='yellow')

        try:
            src = field.method.format_test(header.header)
        except AttributeError as e:
            pass
        else:
            fbuild.logger.log(src, verbose=1)

        return False

def test_header(builder, header_class):
    header = header_class(builder)

    passed = 0
    total = 0

    for result in fbuild.scheduler.map(
            functools.partial(test_field, header),
            (f for n, f in header.fields())):
        total += 1
        if result:
            passed += 1

    return passed, total

def test_module(builder, module):
    headers = []
    for name in dir(module):
        header = getattr(module, name)
        if isinstance(header, type) and issubclass(header, config.Test):
            headers.append(header)

    passed = 0
    total = 0
    for p, t in fbuild.scheduler.map(
            functools.partial(test_header, builder),
            headers):
        passed += p
        total += t
    return passed, total

def build():
    c_static = fbuild.builders.c.guess_static()
    c_shared = fbuild.builders.c.guess_shared()
    cxx_static = fbuild.builders.cxx.guess_static()
    cxx_shared = fbuild.builders.cxx.guess_shared()

    passed = 0
    total = 0

    # c tests
    for builder in c_static, c_shared, cxx_static, cxx_shared:
        for module in c90, c99, posix04, math_h, ieeefp_h:
            p, t = test_module(builder, module)
            passed += p
            total += t

    # c++ tests
    for builder in cxx_static, cxx_shared:
        for module in cxx03, cmath:
            p, t = test_module(builder, module)
            passed += p
            total += t

    fbuild.logger.log('%d/%d tests' % (passed, total))
