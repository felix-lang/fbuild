import argparse
import optparse
import warnings

import fbuild.target

# ------------------------------------------------------------------------------

class OptparseShimMixin:
    def add_option(self, *args, **kw):
        self._optparse_warn()
        self._optparse_add_option(*args, **kw)

    def add_options(self, option_list):
        self._optparse_warn()
        for option in option_list:
            self._optparse_add_option(option)

    def _optparse_warn(self):
        if self._optparse_already_warned:
            return

        warnings.warn('optparse-style API is deprecated; use argparse API instead',
                      fbuild.Deprecation, stacklevel=3)
        self._optparse_already_warned = True

    def _optparse_add_option(self, *args, **kw):
        TYPE_MAP = {
            'string': str,
            'int': int,
            'choice': str,
            'float': float,
            'complex': complex,
        }

        if len(args) >= 1 and isinstance(args[0], optparse.Option):
            option, args = args[0], args[1:]
            for attr in option.ATTRS:
                if attr.startswith('callback'):
                    continue
                elif attr == 'default':
                    default = getattr(option, attr)
                    if default != ('NO', 'DEFAULT'):
                        kw[attr] = default
                elif attr == 'type':
                    ty = getattr(option, attr)
                    if ty is not None:
                        kw[attr] = TYPE_MAP[ty]
                else:
                    value = getattr(option, attr)
                    if value is not None:
                        kw[attr] = value

            args += tuple(option._short_opts + option._long_opts)

        self.add_argument(*args, **kw)

class _ArgumentGroup(argparse._ArgumentGroup, OptparseShimMixin):
    def __init__(self, *args, **kw):
        super(_ArgumentGroup, self).__init__(*args, **kw)
        self._optparse_already_warned = True

class ArgumentParser(argparse.ArgumentParser, OptparseShimMixin):
    def __init__(self, *args, **kw):
        super(ArgumentParser, self).__init__(*args, **kw)
        self._optparse_already_warned = False

    def add_option_group(self, *args, **kw):
        self._optparse_warn()

        group = _ArgumentGroup(self, *args, **kw)
        self._action_groups.append(group)
        return group


# ------------------------------------------------------------------------------

def make_parser():
    description = """
    Fbuild is a new kind of build system that is designed around caching
    instead of tree evaluation.
    """

    epilog = '\nTargets:\n{}\n'.format(fbuild.target.help_string())

    parser = ArgumentParser(description=description, epilog=epilog)

    parser.add_argument('targets', nargs='*', default=['build'],
                        help='The targets to build')

    parser.add_argument('--version', action='version', version=fbuild.__version__)
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='print out extra debugging info')
    parser.add_argument('-j', '--jobs', dest='threadcount', metavar='N', type=int,
                        default=1, help='Allow N jobs at once')
    parser.add_argument('--no-color', action='store_true', default=False,
                        help='do not use colors')
    parser.add_argument('--nocolor', action='store_true', default=False,
                        help='deprecated alias of --no-color')
    parser.add_argument('--show-threads', action='store_true', default=False,
                        help='show which thread is running which command')
    parser.add_argument('--rebuild', dest='force_rebuild', action='store_true',
                        default=False, help='force rebuilding everything')
    parser.add_argument('--configure', dest='force_configuration', action='store_true',
                        default=False, help='deprecated alias of --rebuild')
    parser.add_argument('--buildroot', default='build',
                        help='where to store the build files')
    parser.add_argument('--state-file', default=None,
                        help='the name of the state file ' \
                              '(default: buildroot/fbuild-state.db for pickle engine, ' \
                              'buildroot/fbuild-state.sqldb for sqlite engine)')
    parser.add_argument('--log-file', default='fbuild.log',
                        help='the name of the log file')
    parser.add_argument('--dump-state', action='store_true', default=False,
                        help='print the state database')
    parser.add_argument('--clean', dest='clean_buildroot', action='store_true',
                        default=False, help='clean the build directory')
    parser.add_argument('--delete-function',
                        help='delete cached data for the specified function')
    parser.add_argument('--delete-file',
                        help='delete cached data for the specified file')
    parser.add_argument('--do-not-save-database', action='store_true', default=False,
                        help='do not save the results of the database (for testing)')
    parser.add_argument('--explain-database', action='store_true', default=False,
                        help='explain why a function was not cached')
    parser.add_argument('--database-engine', choices=('pickle', 'sqlite', 'cache'),
                        default='pickle', help='which database engine to use')
    parser.add_argument('--no-warnings', action='store_true', default=False,
                        help='suppress warnings for the build script')

    return parser
