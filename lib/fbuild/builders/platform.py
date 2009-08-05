import os

import fbuild
import fbuild.builders
import fbuild.db

# ------------------------------------------------------------------------------

class UnknownPlatform(fbuild.ConfigFailed):
    def __init__(self, platform=None):
        self.platform = platform

    def __str__(self):
        if self.platform is None:
            return 'cannot determine platform'
        else:
            return 'unknown platform: "%s"' % self.platform

# ------------------------------------------------------------------------------

archmap = {
    'irix':      {'posix', 'irix'},
    'irix64':    {'posix', 'irix', 'irix64'},
    'unix':      {'posix'},
    'posix':     {'posix'},
    'linux':     {'posix', 'linux'},
    'gnu/linux': {'posix', 'linux'},
    'solaris':   {'posix', 'solaris'},
    'sunos':     {'posix', 'solaris', 'sunos'},
    'cygwin':    {'posix', 'cygwin'},
    'nocygwin':  {'posix', 'cygwin', 'nocygwin'},
    'mingw':     {'posix', 'mingw'},
    'windows':   {'windows', 'win32'},
    'nt':        {'windows', 'win32', 'nt'},
    'win32':     {'windows', 'win32'},
    'win64':     {'windows', 'win64'},
    'windows32': {'windows', 'win32'},
    'windows64': {'windows', 'win64'},
    'freebsd':   {'posix', 'bsd', 'freebsd'},
    'netbsd':    {'posix', 'bsd', 'netbsd'},
    'openbsd':   {'posix', 'bsd', 'openbsd'},
    'darwin':    {'posix', 'bsd', 'darwin', 'macosx'},
    'osx':       {'posix', 'bsd', 'darwin', 'macosx'},

    'iphone':           {'posix', 'bsd', 'darwin', 'iphone'},
    'iphone-sim':       {'posix', 'bsd', 'darwin', 'iphone', 'simulator'},
    'iphone-simulator': {'posix', 'bsd', 'darwin', 'iphone', 'simulator'},
}

# ------------------------------------------------------------------------------

@fbuild.db.caches
def platform(arch=None):
    """L{platform} returns a platform set that describes the various features
    of the specified I{platform}. If I{platform} is I{None}, try to determine
    which platform the system is and return that value. If the platform cannot
    be determined, return I{None}."""
    fbuild.logger.check('determining platform')
    if arch is None:
        # First lets see if uname exists
        try:
            uname = fbuild.builders.find_program(['uname'], quieter=1)
        except fbuild.builders.MissingProgram:
            # Maybe we're on windows. Let's just use what python thinks is the
            # platform.
            arch = os.name
        else:
            # We've got uname, so let's see what platform it thinks we're on.
            try:
                stdout, stderr = fbuild.execute((uname, '-s'), quieter=1)
            except fbuild.ExecutionError:
                # Ack, that failed too. Just fall back to python.
                arch = os.name
            else:
                arch = stdout.decode('utf-8').strip().lower()

    try:
        architecture = archmap[arch]
    except KeyError:
        fbuild.logger.failed()
        raise UnknownPlatform(arch)
    else:
        fbuild.logger.passed(architecture)
        return architecture

# ------------------------------------------------------------------------------

def obj_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '.obj'
    else:
        return '.o'

# ------------------------------------------------------------------------------

def static_obj_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '_static.obj'
    else:
        return '.o'

def static_lib_prefix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return ''
    else:
        return 'lib'

def static_lib_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '.lib'
    else:
        return '.a'

# ------------------------------------------------------------------------------

def shared_obj_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '_shared.obj'
    else:
        return '.os'

def shared_lib_prefix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return ''
    else:
        return 'lib'

def shared_lib_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '.dll'
    elif 'darwin' in arch:
        return '.dylib'
    else:
        return '.so'

# ------------------------------------------------------------------------------

def exe_suffix(arch=None):
    arch = platform(arch)
    if 'windows' in arch:
        return '.exe'
    else:
        return ''
