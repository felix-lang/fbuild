import os
import operator
import pickle

import fbuild.builders.c
import fbuild.builders.cxx
import fbuild.config as config
import fbuild.config.c.c90 as c90
import fbuild.config.c.c99 as c99

# ------------------------------------------------------------------------------

def test_header(header_class, builder, passed, total):
    header = header_class(builder)

    for key in sorted(header.__meta__.fields,
            key=operator.attrgetter('__name__')):
        test = getattr(header_class, key.__name__, None)
        total += 1
        if getattr(header, key.__name__):
            passed += 1
        else:
            fbuild.logger.check('failed test:',
                '%s.%s.%s' % (
                    header_class.__module__,
                    header_class.__name__,
                    key.__name__),
                color='yellow')

            try:
                src = test.format_test(header.header)
            except AttributeError:
                pass
            else:
                fbuild.logger.log(src, verbose=1)

    return passed, total


def build():
    total = 0
    passed = 0

    for lang in fbuild.builders.c, fbuild.builders.cxx:
        for builder in lang.guess_static(), lang.guess_shared():
            for module in c90, c99:
                for name in dir(module):
                    header = getattr(module, name)
                    if \
                            isinstance(header, type) and \
                            issubclass(header, config.Test):
                        passed, total = test_header(
                            header, builder, passed, total)

    print('%d/%d tests' % (passed, total))
