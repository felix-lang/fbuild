from fbuild import logger, ConfigFailed
from fbuild.path import find_in_paths, import_function

# -----------------------------------------------------------------------------

class MissingProgram(ConfigFailed):
    def __init__(self, program):
        self.program = program

    def __str__(self):
        return 'cannot find "%s"' % self.program

# -----------------------------------------------------------------------------

def find_program(names):
    for name in names:
        logger.check('checking for program ' + name)

        if find_in_paths(name):
            logger.passed('ok %s' % name)
            return name
        else:
            logger.failed('not found')

    raise ConfigFailed('failed to find any of ' + str(names))

def run_tests(self, tests):
    for test in tests:
        test = import_function(test)
        test(self)

def run_optional_tests(self, tests):
    for test in tests:
        test = import_function(test)
        try:
            test(self)
        except ConfigFailed:
            pass
