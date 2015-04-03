#!/bin/bash

errc=0

fail() {
    errc=1
}

cd tests
./run_tests.py
cd ../examples
for dir in */; do
    cd $dir
    fbuild || fail
    cd ..
done

exit $errc
