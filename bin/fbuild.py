#!/usr/bin/env python3.0

import os
import sys
import pickle
from optparse import OptionParser, make_option
import pprint

import fbuild
import fbuild.scheduler

import fbuildroot

# -----------------------------------------------------------------------------

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
        make_option('--config-file',
            action='store',
            default='config.db',
            help='the name of the config file (default buildroot/config.db)'),
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
    options.buildroot = fbuild.Path(options.buildroot)
    options.config_file = options.buildroot / options.config_file

    # make sure the buildroot exists before running
    fbuild.buildroot = options.buildroot
    fbuild.buildroot.make_dirs()

    # load the logger options into the logger
    fbuild.logger.verbose = options.verbose
    fbuild.logger.nocolor = options.nocolor
    fbuild.logger.show_threads = options.show_threads

    # construct the global scheduler
    fbuild.scheduler = fbuild.scheduler.Scheduler(options.threadcount)

    # -------------------------------------------------------------------------
    # get the configuration

    try:
        if options.force_configuration or not options.config_file.exists():
            # we need to reconfigure, so just use a empty root environment
            env = {}

            # make sure the configuration directory exists
            options.config_file.parent.make_dirs()

            fbuildroot.configure(env, options)

            fbuild.logger.log('saving config')

            with open(options.config_file, 'wb') as f:
                pickle.dump(env, f)

            fbuild.logger.log('-' * 79, color='blue')

        else:
            # reuse the environment from the last run
            with open(options.config_file, 'rb') as f:
                env = pickle.load(f)
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1

    # -------------------------------------------------------------------------

    try:
        # check if we're viewing or manipulating the config
        if options.config_dump:
            # print out the entire config
            pprint.pprint(env)
            return 0

        if options.config_query:
            # print out just a subset of the configuration
            d = env
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
            d = env
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
        fbuildroot.build(env, options)
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1
    finally:
        # re-save the environment
        with open(options.config_file, 'wb') as f:
            pickle.dump(env, f)

    return 0

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
