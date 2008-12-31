#!/usr/bin/env python3.0
import os
import optparse
import shutil
import subprocess
import sys

parser = optparse.OptionParser()
parser.add_option('--clean',
    action='store_true',
    help='clean build files first')

options, args = parser.parse_args()

for d in 'c', 'cxx', 'db', 'ocaml', 'simple', 'substitute':
    build_dir = os.path.join(d, 'build')
    if options.clean and os.path.exists(build_dir):
        print('cleaning:', d)
        shutil.rmtree(build_dir)

    print('running example:', d)
    print()
    subprocess.call(os.path.join('..', '..', 'fbuild-light'), cwd=d, shell=True)
    print()
    print('-' * 50)
    print()
