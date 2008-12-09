#!/usr/bin/env python3.0

import os
import sys
import pickle
from optparse import OptionParser, make_option
import pprint

import fbuild
import fbuild.path
import fbuild.scheduler

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
        make_option('--config-dump',
            action='store_true',
            default=False,
            help='print the config database'),
        make_option('--config-query',
            action='store',
            help='query the config database'),
        make_option('--config-remove',
            action='store',
            help='delete a key in the config'),
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

    # make sure the buildroot exists before running
    fbuild.buildroot = options.buildroot
    fbuild.buildroot.makedirs()

    # load the logger options into the logger
    fbuild.logger.file = open(options.log_file, 'w')
    fbuild.logger.verbose = options.verbose
    fbuild.logger.nocolor = options.nocolor
    fbuild.logger.show_threads = options.show_threads

    # construct the global scheduler
    fbuild.scheduler = fbuild.scheduler.Scheduler(options.threadcount)

    # store the options in fbuild
    fbuild.options = options

    # -------------------------------------------------------------------------
    # get the configuration

    try:
        if options.force_configuration or not options.state_file.exists():
            # we need to reconfigure, so don't try to load the environment.

            # make sure the state file directory exists
            options.state_file.parent.makedirs()
        else:
            # reuse the environment from the last run
            with open(options.state_file, 'rb') as f:
                fbuild.env.__setstate__(pickle.load(f))
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1

    # -------------------------------------------------------------------------

    try:
        # check if we're viewing or manipulating the config
        if options.config_dump:
            # print out the entire config
            pprint.pprint(fbuild.env._builder_state)
            return 0

        if options.config_query:
            # print out just a subset of the configuration
            d = fbuild.env._builder_state
            try:
                for key in options.config_query.split():
                    d = d[key]
            except KeyError:
                raise fbuild.Error(
                    'missing config value for %s' % options.config_query)
            else:
                pprint.pprint(d)
                return 0

        if options.config_remove:
            keys = options.config_remove.split()
            d = fbuild.env._builder_state
            try:
                for key in keys[:-1]:
                    d = d[key]
                del d[keys[-1]]
                return 0
            except KeyError:
                raise fbuild.Error(
                    'missing config value for %s' % options.config_remove)
                return 1

        # ---------------------------------------------------------------------
        # finally, do the build
        fbuildroot.build()
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1
    finally:
        # Compiling the pickle string could raise an exception, so we'll pickle
        # write to a temporary file first, then write it out to the state file.
        with open(options.state_file + '.tmp', 'wb') as f:
            pickle.dump(fbuild.env.__getstate__(), f)

        # Save the state to the state file.
        os.rename(options.state_file + '.tmp', options.state_file)

    return 0

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
