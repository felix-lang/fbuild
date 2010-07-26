from optparse import OptionParser, make_option

# ------------------------------------------------------------------------------

def make_parser():
    description = """
    Fbuild is a new kind of build system that is designed around caching
    instead of tree evaluation.
    """

    parser = OptionParser(
        version=fbuild.__version__,
        usage='%prog [options]',
        description=description)

    parser.add_options([
        make_option('-v', '--verbose',
            action='count',
            default=0,
            help='print out extra debugging info'),
        make_option('--show',
            action='count',
            default=1,
            help='print out extra debugging info'),
        make_option('-j', '--jobs',
            dest='threadcount',
            metavar='N',
            type='int',
            default=1,
            help='Allow N jobs at once'),
        make_option('--nocolor',
            action='store_true',
            default=False,
            help='Do not use colors'),
        make_option('--show-threads',
            action='store_true',
            default=False,
            help='Show which thread is running which command'),
        make_option('--configure',
            dest='force_configuration',
            action='store_true',
            default=False,
            help='force reconfiguration'),
        make_option('--buildroot',
            action='store',
            default='build',
            help='where to store the build files (default build)'),
        make_option('--state-file',
            action='store',
            default='fbuild-state.db',
            help='the name of the state file ' \
                 '(default buildroot/fbuild-state.db)'),
        make_option('--log-file',
            action='store',
            default='fbuild.log',
            help='the name of the log file (default fbuild.log)'),
        make_option('--dump-state',
            action='store_true',
            default=False,
            help='print the state database'),
        make_option('--clean',
            dest='clean_buildroot',
            action='store_true',
            default=False,
            help='clean the build directory'),
        make_option('--clear-function',
            action='store',
            help='clear cached data for the specified function'),
        make_option('--clear-file',
            action='store',
            help='clear cached data for the specified file'),
        make_option('--do-not-save-database',
            action='store_true',
            default=False,
            help='do not save the results of the database for testing.'),
    ])

    return parser
