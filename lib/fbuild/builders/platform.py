import platform
import os

import fbuild
import fbuild.db
import fbuild.functools

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
    'cygwin':    {'posix', 'cygwin', 'windows'},
    'nocygwin':  {'posix', 'cygwin', 'nocygwin', 'windows'},
    'mingw':     {'posix', 'mingw', 'windows'},
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
def guess_platform(ctx, arch=None):
    """L{guess_platform} returns a platform set that describes the various
    features of the specified I{platform}. If I{platform} is I{None}, try to
    determine which platform the system is and return that value. If the
    platform cannot be determined, return I{None}."""

    import fbuild.builders

    ctx.logger.check('determining platform')
    if arch is None:
        # If we're on Windows, then don't even try uname
        if os.name == 'nt':
            res = archmap[platform.system().lower()]
            ctx.logger.passed(res)
            return frozenset(res)
        # Let's see if uname exists
        try:
            uname = fbuild.builders.find_program(ctx, ['uname'], quieter=1)
        except fbuild.builders.MissingProgram:
            # Maybe we're on windows. Let's just use what python thinks is the
            # platform.
            #arch = os.name
            arch = platform.system().lower()
        else:
            # We've got uname, so let's see what platform it thinks we're on.
            try:
                stdout, stderr = ctx.execute((uname, '-s'), quieter=1)
            except fbuild.ExecutionError:
                # Ack, that failed too. Just fall back to python.
                #arch = os.name
                arch = platform.system().lower()
            else:
                arch = stdout.decode('utf-8').strip().lower()

    if arch.startswith('mingw32'):
        arch = 'mingw'
    elif arch.startswith('cygwin'):
        arch = 'cygwin'
    try:
        architecture = archmap[arch]
    except KeyError:
        ctx.logger.failed()
        raise UnknownPlatform(arch)
    else:
        ctx.logger.passed(architecture)
        return frozenset(architecture)

# ------------------------------------------------------------------------------

def obj_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if 'windows' in platform:
        return '.obj'
    else:
        return '.o'

# ------------------------------------------------------------------------------

def static_obj_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if 'windows' in platform:
        return '_static.obj'
    else:
        return '.o'

def static_lib_prefix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if 'windows' in platform and 'mingw' not in platform:
        return ''
    else:
        return 'lib'

def static_lib_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if 'windows' in platform and 'mingw' not in platform:
        return '.lib'
    else:
        return '.a'

# ------------------------------------------------------------------------------

def shared_obj_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if 'windows' in platform:
        return '_shared.obj'
    else:
        return '.os'

def shared_lib_prefix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if platform & {'windows', 'mingw', 'cygwin'}:
        return ''
    else:
        return 'lib'

def shared_lib_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if platform & {'windows', 'mingw', 'cygwin'}:
        return '.dll'
    elif 'darwin' in platform:
        return '.dylib'
    else:
        return '.so'

# ------------------------------------------------------------------------------

def exe_suffix(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if platform & {'windows'}:
        return '.exe'
    else:
        return ''

# ------------------------------------------------------------------------------

def runtime_env_libpath(ctx, platform=None):
    platform = platform if platform else guess_platform(ctx)
    if platform & {'windows'} and not platform & {'cygwin'}:
        return 'PATH'
    elif 'darwin' in platform:
        return 'DYLD_LIBRARY_PATH'
    else:
        return 'LD_LIBRARY_PATH'

# ------------------------------------------------------------------------------

def platform_match(platform, matcher):
    required_present = set(p for p in matcher if not p.startswith('!'))
    required_nonpresent = set(p for p in matcher if p.startswith('!'))

    return required_present <= platform and not platform & required_nonpresent


def parse_platform_options(ctx, platform, platform_options, kwargs):
    types_supporting_operations = (str, list, tuple, set)

    if platform is None:
        platform = guess_platform(ctx)

    for matcher, options in platform_options:
        if platform_match(platform, matcher):
            # It matches! Use it to update kwargs.
            for key, modifier in options.items():
                if key[-1] in '+-':
                    # Addition/removal.
                    operation = key[-1]
                    key = key[:-1]

                    assert isinstance(modifier, types_supporting_operations), \
                           "type '%s' does not support + and - operations" % type(modifier)

                    value = kwargs.get(key)
                    if value is None:
                        value = type(modifier)()

                    if operation == '+':
                        value += modifier
                    elif operation == '-':
                        filtered = (x for x in value if x not in modifier)

                        if isinstance(value, str):
                            value = ''.join(filtered)
                        else:
                            value = type(value)(filtered)
                    else:
                        assert False

                    kwargs[key] = value
                else:
                    kwargs[key] = modifier


def auto_platform_options(pass_platform=False):
    def _decorator(func):
        @fbuild.functools.wraps(func)
        def _wrapper(*args, **kw):
            inner = kw.pop('__FBUILD_INNER')
            from fbuild.context import Context

            # XXX: This check for methods is stupid, stupid, stupid.
            if not args:
                ctx = None
            elif not isinstance(args[0], Context) and \
                 isinstance(getattr(args[0], 'ctx', None), Context):
                ctx = args[0].ctx
            elif len(args) > 1 and isinstance(args[1], Context):
                ctx = args[1]
            else:
                ctx = args[0]

            if ctx is not None:
                parse_platform_options(ctx, kw.get('platform', None),
                                       kw.pop('platform_options', []), kw)
            if not pass_platform:
                kw.pop('platform', None)
            return inner(*args, **kw)

        return _wrapper

    return _decorator
