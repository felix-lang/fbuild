#!/usr/bin/env python3.0

import pprint
import signal
import sys
from optparse import OptionParser, make_option

import fbuild
import fbuild.db
import fbuild.path
import fbuild.sched

# ------------------------------------------------------------------------------

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = OptionParser(option_list=[
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

    # -------------------------------------------------------------------------
    # let the fbuildroot modify the optparse parser before parsing

    import fbuildroot

    try:
        pre_options = fbuildroot.pre_options
    except AttributeError:
        pass
    else:
        parser = pre_options(parser) or parser

    options, args = parser.parse_args(argv)

    # -------------------------------------------------------------------------
    # let the fbuildroot modify the optparse parser after parsing

    try:
        post_options = fbuildroot.post_options
    except AttributeError:
        pass
    else:
        options, args = post_options(options, args) or (options, args)

    # -------------------------------------------------------------------------
    # prepare all the global variables

    # convert the option paths into Path objects
    options.buildroot = fbuild.path.Path(options.buildroot)
    options.state_file = options.buildroot / options.state_file

    # --------------------------------------------------------------------------

    if options.clean_buildroot:
        try:
            options.buildroot.rmtree()
        except OSError:
            pass
        return

    # --------------------------------------------------------------------------

    # make sure the buildroot exists before running
    fbuild.buildroot = options.buildroot
    fbuild.buildroot.makedirs()

    # load the logger options into the logger
    fbuild.logger.file = open(options.buildroot / options.log_file, 'w')
    fbuild.logger.verbose = options.verbose
    fbuild.logger.nocolor = options.nocolor
    fbuild.logger.show_threads = options.show_threads

    # construct the global scheduler
    fbuild.scheduler = fbuild.sched.Scheduler(options.threadcount)

    # store the options in fbuild
    fbuild.options = options

    # -------------------------------------------------------------------------
    # get the configuration

    # make sure the state file directory exists
    options.state_file.parent.makedirs()

    if not options.force_configuration and options.state_file.exists():
        # We aren't reconfiguring, so load the old database.
        fbuild.db.database.load(options.state_file)

    # -------------------------------------------------------------------------

    try:
        # check if we're viewing or manipulating the state
        if options.dump_state:
            # print out the entire state
            pprint.pprint(fbuild.db.database.__dict__)
            return 0

        if options.clear_function:
            if not fbuild.db.database.clear_function(options.clear_function):
                raise fbuild.Error('function %r not cached' %
                        options.clear_function)
            return 0

        if options.clear_file:
            if not fbuild.db.database.clear_file(options.clear_file):
                raise fbuild.Error('file %r not cached' % options.clear_file)

            return 0

        # ---------------------------------------------------------------------
        # finally, do the build
        fbuildroot.build()
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1
    except KeyboardInterrupt:
        # It appears that we can't reliably shutdown the scheduler's threads
        # when SIGINT is emitted, because python may raise KeyboardInterrupt
        # between the finally and the mutex.release call.  So, we can find
        # ourselves exiting functions with the lock still held.  This could
        # then cause deadlocks if that lock was ever acquired again.  Oiy.
        raise
    else:
        # No exception occurred, so let us be good and shut down the scheduler.
        fbuild.scheduler.shutdown()
    finally:
        if not options.do_not_save_database:
            # Remove the signal handler so that we can't interrupt saving the
            # db.
            prev_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                fbuild.db.database.save(options.state_file)
            finally:
                signal.signal(signal.SIGINT, prev_handler)

    return 0

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
