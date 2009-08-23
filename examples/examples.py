#!/usr/bin/env python3.1
import os
import optparse
import subprocess
import sys

parser = optparse.OptionParser()
parser.add_option('--clean',
    action='store_true',
    help='clean build files first')

options, args = parser.parse_args()

examples_dir = os.path.dirname(__file__) or os.getcwd()
for d in os.listdir(examples_dir):
    d = os.path.join(examples_dir, d)

    if not os.path.isdir(d):
        continue

    if options.clean:
        print('cleaning:', d)
        subprocess.call('%s %s --clean' %
            (sys.executable, os.path.join('..', '..', 'fbuild-light')),
            cwd=d, shell=True)

    print('running example:', d)
    print()
    subprocess.call('%s %s' %
        (sys.executable, os.path.join('..', '..', 'fbuild-light')),
        cwd=d, shell=True)
    print()
    print('-' * 50)
    print()
