#!/usr/bin/env python3.0

import os
import sys
import pickle

# -----------------------------------------------------------------------------

def main(argv=None):
    if argv is None:
        argv = sys.argv

    from optparse import OptionParser, make_option
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

    import fbuildroot
    try:
        pre_options = fbuildroot.pre_options
    except AttributeError:
        pass
    else:
        parser = pre_options(parser) or parser

    options, args = parser.parse_args(argv)

    options.config_file = os.path.join(options.buildroot, options.config_file)

    try:
        post_options = fbuildroot.post_options
    except AttributeError:
        pass
    else:
        options, args = post_options(options, args) or (options, args)

    import fbuild
    fbuild.buildroot = options.buildroot
    fbuild.logger.verbose = options.verbose
    fbuild.logger.nocolor = options.nocolor
    fbuild.logger.show_threads = options.show_threads

    import fbuild.scheduler
    fbuild.scheduler = fbuild.scheduler.Scheduler(options.threadcount)

    # -------------------------------------------------------------------------

    try:
        config = configure_package(fbuildroot, options)

    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1

    # -------------------------------------------------------------------------

    try:
        if options.config_dump:
            import pprint
            pprint.pprint(config)
            return 0

        if options.config_query:
            import pprint
            d = config
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
            d = config
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

        fbuildroot.build(config, options)
    except fbuild.Error as e:
        fbuild.logger.log(e, color='red')
        return 1
    finally:
        # re-save the config
        with open(options.config_file, 'wb') as f:
            pickle.dump(config, f)

    return 0

def configure_package(package, options):
    import fbuild

    if options.force_configuration or not os.path.exists(options.config_file):
        config = {}
        package.configure(config, options)

        fbuild.logger.log('saving config')

        config_dir = os.path.dirname(options.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        with open(options.config_file, 'wb') as f:
            pickle.dump(config, f)

        fbuild.logger.log('-' * 79, color='blue')
    else:
        with open(options.config_file, 'rb') as f:
            config = pickle.load(f)

    return config

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
