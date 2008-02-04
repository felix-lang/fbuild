#!/usr/bin/env python3.0

import os
import sys
import optparse
from optparse import OptionParser, make_option

import fbuild.system
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
        make_option('--configure',
            dest='force_configuration',
            action='store_true',
            default=False,
            help='force reconfiguration'),
    ])

    try:
        pre_options = fbuildroot.pre_options
    except AttributeError:
        pass
    else:
        parser = pre_options(parser) or parser

    options, args = parser.parse_args(argv)

    try:
        post_options = fbuildroot.post_options
    except AttributeError:
        pass
    else:
        options, args = post_options(options, args) or (options, args)

    system = fbuild.system.System('config.yaml',
        verbose=options.verbose,
        threadcount=options.threadcount,
        nocolor=options.nocolor,
        force_configuration=options.force_configuration,
    )

    try:
        system.run_package(fbuildroot, options)
    except fbuild.ConfigFailed:
        return 1

    return 0

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
