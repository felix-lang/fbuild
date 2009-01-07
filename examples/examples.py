#!/usr/bin/env python3.0
import os
import optparse
import subprocess
import sys

parser = optparse.OptionParser()
parser.add_option('--clean',
    action='store_true',
    help='clean build files first')

options, args = parser.parse_args()

for d in 'c', 'cxx', 'db', 'ocaml', 'simple', 'substitute':
    if options.clean:
        print('cleaning:', d)
        subprocess.call('%s --clean' % os.path.join('..', '..', 'fbuild-light'), cwd=d, shell=True)

    print('running example:', d)
    print()
    subprocess.call(os.path.join('..', '..', 'fbuild-light'), cwd=d, shell=True)
    print()
    print('-' * 50)
    print()
