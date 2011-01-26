Fbuild Build System
===================

Overview
========

Fbuild is a new kind of build system that is designed around caching instead of
declarative tree evaluation like Make or SCons. This allows you to write your
build system in a more natural procedural way. Here's a simple example for
compiling a C file named `helloworld.c`:

    #include <stdio.h>
    int main() {
        printf("hello world!\n");
        return 0;
    }

To compile this with fbuild, you write a python 3 driver script called
`fbuildroot.py`:

    import fbuild.builders.c
    def build(ctx):
        builder = fbuild.builders.c.guess_shared(ctx)
        exe = builder.build_exe('helloworld', ['helloworld.c'])

        ctx.logger.log(' * running ' + exe)
        ctx.execute([exe])

When run with `fbuild` (or `fbuild-light` if you want to run Fbuild out of the
repository), Fbuild will print out:

    $ fbuild
    determining platform     : {'bsd', 'darwin', 'macosx', 'posix'}
    looking for program gcc   : ok /usr/bin/gcc
    checking gcc              : ok
    checking gcc with -fPIC   : ok
    checking gcc with -dynamiclib : ok
    checking if gcc -fPIC can make objects : ok
    checking if gcc -fPIC can make libraries: ok
    checking if gcc -fPIC can make exes     : ok
    checking if gcc -fPIC can link lib to exe: ok
     * gcc -fPIC                            : helloworld.c -> build/helloworld.os
     * gcc                                  : build/helloworld.os -> build/helloworld
     * running build/helloworld
    hello world!

Fbuild provides a very large feature set beyond just simple building:

 * Linux, Apple and Windows support
 * C, C++, OCaml, Java, Scala, Bison, and Felix builders
 * Multilevel namespaces for builders
 * Simple creation of new builders
 * Extensive configuration system for c90, c99, most of posix, and other
   libraries
 * On-demand configuration
 * Multithreaded building
 * Cross compiling
 * Detects file changes via file digests
 * Pretty output
 * Very speedy

See the [wiki](https://github.com/erickt/fbuild/wiki) for more documentation.
For more advanced examples, please see `examples/` in the git repository. To
run the examples::

    $ cd examples
    $ python3 examples.py

Install
=======

To install Fbuild from source, first you must install [Python
3](http://docs.python.org/py3k). Next you can run Fbuild's installer::

    $ python3 setup.py install


Unit Tests
==========

To run the unit tests::

    $ cd tests
    $ python3 run_tests.py

If any tests fail, please copy and paste the output and send the details to the
[fbuild mailing list](http://groups.google.com/group/fbuild).
