#!/bin/bash

errc=0

fail() {
    errc=1
}

cd tests
./run_tests.py
cd ../examples
for dir in */; do
    [ $dir = "config/" ] && continue # this is bugged under Travis for some reason
    echo "Running example $dir"
    cd $dir
    ../../fbuild-light || fail
    cd ..
done

exit $errc
