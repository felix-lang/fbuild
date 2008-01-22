import os
import types
import functools
import yaml

import fbuild
import fbuild.path
import fbuild.builders

# -----------------------------------------------------------------------------

def find_program(system, names, *args, **kwargs):
    for name in names:
        system.check('checking for program ' + name)

        program = fbuild.path.find_in_paths(name, *args, **kwargs)
        if program:
            system.log('ok %s' % program, color='green')
            return program
        else:
            system.log('not found', color='yellow')

    raise fbuild.ConfigFailed('failed to find any of ' + str(names))
