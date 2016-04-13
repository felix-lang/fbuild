Manual
======

Basics
******

Getting Started
^^^^^^^^^^^^^^^

This manual is for the most recent version of Fbuild from Git. In order to get it,
just run::
   
   $ git clone https://github.com/felix-lang/fbuild.git
   $ cd fbuild
   $ python3 setup.py install

You can also use Fbuild without installing it by running the ``fbuild-light``
script.

Compiling C
^^^^^^^^^^^

Let's start with a simple build script: it just builds a "Hello, world!" program
written in C. Here's the C code:

.. code-block:: c
   
   #include <stdio.h>
   
   int main() {
       puts("Hello, world!");
       return 0;
   }

and the Fbuild build script:

.. code-block:: python
   
   from fbuild.builders.c import guess_static
   
   def build(ctx):
       builder = guess_static(ctx)
       builder.build_exe('hello', ['hello.c'])

It's pretty simple. First, ``guess_static`` is imported. That function returns a
new builder for building C programs (we'll get to builders in a moment). Then, the
script defines a ``build`` function that takes an object of type
``fbuild.context.Context`` (``ctx``). That object is kind of like the "build
engine." The next line calls ``guess_static``, and the line after calls the
``build_exe`` method. It can take several keyword arguments, but the only two
positional ones are the output file (``hello``) and a list of source files
(``['hello.c']``). Let's run it::

   ryan@DevPC-LX:~/stuff/fbuild/playground/doc$ fbuild
   determining platform     : {'linux', 'posix'}
   looking for clang        : ok /home/ryan/stuff/Downloads/clang+llvm-3.8.0-x86_64-linux-gnu-ubuntu-14.04/bin/clang
   checking clang           : ok
   looking for ar           : ok /usr/bin/ar
   looking for ranlib       : ok /usr/bin/ranlib
   checking if clang can make objects : ok
   checking if clang can make libraries : ok
   checking if clang can make exes      : ok
   checking if clang can link lib to exe : ok
    * clang                              : hello.c -> build/obj/hello/hello.o
    * clang                              : build/obj/hello/hello.o -> build/hello
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc$ 

That just:

- Detected my C compiler and the associated utilities (``ar`` and ``ranlib``).
- Tested it.
- Built our program.

Builders
^^^^^^^^

In Fbuild, a *builder* is an object that...builds stuff. In the last example, the
builder could build C executables and libraries. Most of Fbuild revolves around
builders, and all of them are located within ``fbuild.builders``.

Rewind: The Core of Fbuild
**************************

Graphs and Caching
^^^^^^^^^^^^^^^^^^

Let's take a step back for a moment. How does all this stuff even work??

Conventional build systems usually will function by first building a DAG (directed
acyclic graph) consisting of all the inputs/outputs as nodes and the commands to
create the outputs as edges. Although this allows some nice features (such as
implicit parallelism and cool progress bars), it doesn't allow for some important
things. In particular, if you've ever use Make, you know how painful it can be to
read dependencies from a file. In addition, you can't decide a target's outputs at
run time, and some DAG-based build systems can be either hard to extend, hard to
use for simple projects, or brutally low-level.

Fbuild doesn't use a DAG. It doesn't even use a graph at all. Instead, it uses
something much more powerful: caching. The core idea is that *all your build rules
are really just functions*.

Any attempt to explain this any more would likely fail, so I'll just show an
example. Put this in a new ``fbuildroot.py``:

.. code-block:: python
   
   import fbuild.db
   
   @fbuild.db.caches
   def myfunc(ctx, name):
       print('Hello, %s!' % name)
   
   def build(ctx):
       myfunc(ctx, 'Fbuild world')

I'll explain ``fbuild.db.caches`` in a moment, but for now, note that any function
that you use it on *must* take a context object as its first argument.

When the script is run, the output is what one would expect::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ fbuild
   Hello, Fbuild world!
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ 

However, watch what happens if you run it again::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ fbuild
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ 

Nothing was shown! But why?

``fbuild.db.caches`` will *cache* (or memoize, if you're more familiar with that
term) the given function. That means that, when the function is called, Fbuild
will save its arguments and the result into a database on disk (by default, it's
located in ``build/fbuild.db``). If the function is called again, then, instead of
running it, Fbuild will just return the previous result. This is more obvious
with a slightly different example:

.. code-block:: python
   
   import fbuild.db
   
   @fbuild.db.caches
   def myfunc(ctx, name):
       print('Hello, %s!' % name)
       return 'myfunc was called'
   
   def build(ctx):
       message = myfunc(ctx, 'Fbuild world')
       print(message)

If you run it, this happens::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ fbuild
   Hello, Fbuild world!
   myfunc was called
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ 

Note that the database didn't need to be deleted; Fbuild will automatically
re-run a function if its contents have changed.

Watch what happens if you run it again::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ fbuild
   myfunc was called
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw$ 

When ``myfunc`` was called the first time, it's return value (
``'myfunc was called'``) was saved into the database. On the second run, Fbuild
saw that ``myfunc`` hadn't changed and was being called with the same arguments,
so it just returned the original return value.

You may be wondering what this has to do with build systems. Well, in Fbuild,
almost every internal function is cached like this. Remember ``guess_static``? If
you run that script again, the C compiler won't be re-configured. Fbuild cached
the result of calling ``guess_static`` and loaded it back up from the database.

Dependencies
^^^^^^^^^^^^

All this is really cool, but it doesn't seem that practical at the moment. Build
systems don't just configure builders; they also...well, build stuff. Caching
seems useless for solving this problem, right!

Wrong! Fbuild has several function annotations that you can use to help with this.
Take a look at this build script:

.. code-block:: python
   
   import fbuild.db
   
   @fbuild.db.caches
   def build_a_file(ctx, src: fbuild.db.SRC):
       print('This is supposed to build the file %s...' % src)
   
   def build(ctx):
       build_a_file(ctx, 'myfile')

I'll explain the details in a moment; for now, just know that ``build_a_file`` is
supposed to do something with its input argument ``myfile``. Let's run it::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ fbuild
   Traceback (most recent call last):
     File "/media/ryan/stuff/anaconda/bin/fbuild", line 9, in <module>
       load_entry_point('fbuild==0.2', 'console_scripts', 'fbuild')()
     File "/media/ryan/stuff/fbuild/lib/fbuild/main.py", line 179, in main
       result = build(ctx)
     File "/media/ryan/stuff/fbuild/lib/fbuild/main.py", line 104, in build
       target.function(ctx)
     File "/media/ryan/stuff/fbuild/playground/doc-rw-dep/fbuildroot.py", line 8, in build
       build_a_file(ctx, 'myfile')
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/__init__.py", line 121, in __call__
       result, srcs, dsts = self.call(*args, **kwargs)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/__init__.py", line 125, in call
       return ctx.db.call(self.function, ctx, *args, **kwargs)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/database.py", line 101, in call
       dsts)
     File "/media/ryan/stuff/fbuild/lib/fbuild/rpc.py", line 68, in call
       raise result.result
     File "/media/ryan/stuff/fbuild/lib/fbuild/rpc.py", line 112, in _process
       result.result = self._handler(*args, **kwargs)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/database.py", line 24, in handle_rpc
       return method(*args, **kwargs)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/backend.py", line 42, in prepare
       call_file_digests = self.check_call_files(call_id, srcs)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/backend.py", line 143, in check_call_files
       d, file_id, file_digest = self.check_call_file(call_id, file_name)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/backend.py", line 165, in check_call_file
       dirty, file_id, mtime, digest = self.add_file(file_name)
     File "/media/ryan/stuff/fbuild/lib/fbuild/db/backend.py", line 249, in add_file
       file_mtime = file_path.getmtime()
     File "/media/ryan/stuff/fbuild/lib/fbuild/path.py", line 224, in getmtime
       return os.path.getmtime(self)
     File "/media/ryan/stuff/anaconda/lib/python3.4/genericpath.py", line 55, in getmtime
       return os.stat(filename).st_mtime
   FileNotFoundError: [Errno 2] No such file or directory: Path('myfile')

Whoops! I forgot to create ``myfile``::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ touch myfile
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ fbuild
   This is supposed to build the file myfile...
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ 

As usual, let's also run it again::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ fbuild
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ 

Nothing happened! This is caching at work again.

Now try adding something to ``myfile`` and running it again::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ echo 1234 > myfile
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ fbuild
   This is supposed to build the file myfile...
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ 

``build_a_file`` is run again! Look back at these two lines in ``fbuildroot.py``:

.. code-block:: python
   
   @fbuild.db.caches
   def build_a_file(ctx, src: fbuild.db.SRC):

I already explained how ``fbuild.db.caches`` works. However, the new addition is
the function annotation ``fbuild.db.SRC``. This works with ``fbuild.db.caches`` to
allow for dependency resolution.

When you annotate a function argument with ``fbuild.db.SRC``, you're telling
``fbuild.db.caches`` that the argument is a source file. As already stated, if
you change ``build_a_file`` or change any of its arguments, it will be re-run.
In addition, *if you change the contents of any source file, the function will
also be re-run*. Because I changed the contents of ``myfile``, Fbuild re-ran
``build_a_file``.

Remember ``build_exe``? This is how it works. Although the function itself is
somewhat complex, at it's core, it uses a similar method to this.

You can also create functions that take multiple sources:

.. code-block:: python
   
   import fbuild.db
   
   @fbuild.db.caches
   def build_a_file(ctx, first_source: fbuild.db.SRC, other_sources: fbuild.db.SRCS):
       print('Do something with %s and %s...' % (first_source, other_sources))

   def build(ctx):
       build_a_file(ctx, 'myfile1', ['myfile2', 'myfile3'])

As you might expect by now, ``fbuild.db.SRCS`` takes a list of source files, not
just one.

Nevertheless, this is only part of the equation. A build system usually needs to
also keep track of its output files. Unlike other example scripts, this is
actually not just a toy; it's actually a quite useful function:

.. code-block:: python
   
   import fbuild.db, shutil, io
   
   @fbuild.db.caches
   def merge_files(ctx, srcs: fbuild.db.SRCS, dst: fbuild.db.DST):
       print('Merging files...')
   
       result = io.StringIO()
       for src in srcs:
           with open(src) as f:
               shutil.copyfileobj(f, result)
   
       result.seek(0)
       with open(dst, 'w') as f:
           shutil.copyfileobj(result, f)
   
   def build(ctx):
       merge_files(ctx, ['input1', 'input2'], 'output')

The details of ``merge_files`` don't really matter as much as the function
annotations. Note that another annotation was added: ``fbuild.db.DST``, which
annotates the destination parameter. The results of running it are like you'd
expect::
   
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ echo 1 > input1
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ echo 2 > input2
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ fbuild
   Merging files...
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ cat output 
   1
   2
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-dep$ 

As before, any changes to ``input1`` or ``input2`` will cause ``output`` to be
re-built.

This isn't quite enough, however, but before I go to the next topic, there's one
more basic thing that needs to be covered: paths.

Path Objects
^^^^^^^^^^^^

Remember the error message when I forgot to create ``myfile``? It mentioned that
the missing file was ``Path('myfile')``. The ``Path`` here is for Fbuild's *path
objects*. I won't go over every single detail, but path objects (defined in
``fbuild.path``) are...well, path objects. The class ``fbuild.path.Path`` is a
subclass of ``str``, so it supports all the normal operations of ``str``, and you
can pass it to any normal Python function expecting a string, However, path
objects also have a bunch of methods useful for file system/path manipulation.

For thorough documentation on all the methods, check out `lib/fbuild/path.py <
https://github.com/felix-lang/fbuild/blob/master/lib/fbuild/path.py>_` in the
source code. Here I'll mention just one capability of paths: in order to join
them, you can use ``/``. For instance, ``Path('src') / 'dst'`` returns
``Path('src/dst')`` on Posix and ``Path('src\\dst')`` on Windows.

Rule Destinations and Cached Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Back on topic: recall the very first Fbuild script in the tutorial:

.. code-block:: python
   
   from fbuild.builders.c import guess_static
   
   def build(ctx):
       builder = guess_static(ctx)
       builder.build_exe('hello', ['hello.c'])

See ``builder.build_exe``? That function actually returns a value: the full path
to the resulting executable. The reason is that, usually, the developer doesn't
care where the executable is stored or what extension it has, but they may very
well want to know where it's located. To handle this case, Fbuild supports
annotating the function's *return value* as a destination. For example:

.. code-block:: python
   
   from fbuild.path import Path
   import fbuild.db, shutil
   
   @fbuild.db.caches
   def do_something(ctx, src: fbuild.db.SRC) -> fbuild.db.DST:
       src = Path(src)
       dst = ctx.buildroot / src.replaceext('.out')
       print('Copying %s to %s...' % (src, dst))
       src.copy(dst)
       return dst
   
   def build(ctx):
       do_something(ctx, 'x.in')

Let's run it::

   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-out$ echo 123 > x.in
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-out$ fbuild
   Copying x.in to build/x.out...
   ryan@DevPC-LX:~/stuff/fbuild/playground/doc-rw-out$ 

This script has a lot of new stuff! It uses the ``Path`` objects mentioned in the
previous section. In particular:

- This is the first example script to use ``ctx.buildroot``, which is a ``Path``
  that points to the output directory. In this case, it's ``build``.

- ``Path.replaceext`` replaces the given file extension, e.g.
  ``Path('x.in').replaceext('.out')`` results in ``Path('x.out')``.

- ``Path.copy`` copies the given file. ``Path(src).copy(dst)``` is equivalent to
  ``shutil.copy(src, dst)``.

- **Most importantly,** ``do_something`` returns the resulting output file. This
  will cause Fbuild to place it in the database.

The entirety of Fbuild, including the C builder that I first showed, consists of
what I've just shown here, with three exceptions:

1. In ``fbuild.db``, there's a very important class:
   ``fbuild.db.PersistentObject``. If you want to contain any cached functions
   within a class, the class must derive from ``PersistentObject``, and the cached
   functions should instead use ``cachemethod`` (see below).

2. ``fbuild.db.cachemethod`` is equivalent to ``fbuild.db.caches``, but it is
   instead designed to annotate methods.

3. Sometimes, you may not want to return a whole object. For this case, Fbuild
   provides ``fbuild.record.Record``. A ``Record`` is basically a ``dict``, except
   that you can also set and get keys via attributes. For example, ``my_record.a``
   is equivalent to ``my_record['a']``.

Many examples of this are in the Fbuild source.

Back to a higher level: user interaction and commands
*****************************************************

Logging
^^^^^^^

Of course, a build system is mostly useless without being able to run external
commands. First, I need to mention an important concept of Fbuild that I've
glossed over thus far: logging.

Notice that, in all the above examples, ``print`` was used to print information.
Technically, you're not supposed to do this! In order to handle this, Fbuild
provides ``ctx.logger``. Here's a basic example:

.. code-block:: python
   
   def build(ctx):
       ctx.logger.log('This will be written to the log file: build/fbuild.log.',
                      verbose=1)
       ctx.logger.log('This will be written to the console.')
   
       ctx.logger.log('This will be written to the console in red.', color='red')
       ctx.logger.log('This will be written to the console in a color designated for '
                      'compiling files.', color='compile')
       ctx.logger.log('And for linking files!', color='link')
   
       ctx.logger.check('this is used when configuring various things in Fbuild')
       ctx.logger.passed()
   
       ctx.logger.check('you can also give custom messages and colors', color='blue')
       ctx.logger.passed('it worked!')
   
       ctx.logger.check('things can also fail')
       ctx.logger.failed('dang it!')

and here's the output:

.. image:: http://s23.postimg.org/6exhuh3ff/fbuild_log.png

Finding programs
^^^^^^^^^^^^^^^^

Actually, there's *one* more thing to mention first. A frequently needed
capability of a build system is to locate a program. For instance, you may want
to find the ``awk`` executable on the system. For this, Fbuild has
``fbuild.builders.find_program``. It works like this:

.. code-block:: python
   
   from fbuild.builders import find_program
   
   def build(ctx):
       awk = find_program(ctx, ['awk', 'gawk'])
       print(awk)

It takes two arguments: the context object and a list of programs to search for.
The return value is the first program it found. If none are found, it will throw
an exception of type ``fbuild.ConfigFailed``.

In addition, ``find_program`` is cached, so it won't re-run every single time you
run ``fbuild``.

Executing shell commands
^^^^^^^^^^^^^^^^^^^^^^^^

*Now* comes executing shell commands! Every context object has a method for this:
``execute``. Here's the definition from the source code:

.. code-block:: python
   
   def execute(self, cmd, msg1=None, msg2=None, *,
           color=None,
           quieter=0,
           stdout_quieter=None,
           stderr_quieter=None,
           input=None,
           stdin=None,
           stdout=fbuild.subprocess.PIPE,
           stderr=fbuild.subprocess.PIPE,
           timeout=None,
           env=None,
           runtime_libpaths=None,
           ignore_error=False,
           **kwargs):

That's a lot of arguments! I'll break them down one by one:

- ``cmd`` is the command to run. Although there are some edge cases, in general,
  this should be a list, such as ``['clang', '-o', 'x', 'x.c']``.

- ``msg1``, ``msg2``, and ``color`` will be explained below.

- ``quieter`` is the same as the ``quieter`` argument with ``logger.log``; it
  determines whether or not ``msg1`` and ``msg2`` will be displayed or just sent
  to the log file. In addition, this will be the default value fo
  ``stdout_quieter`` and ``stderr_quieter`` if they are ``None``.

- ``stdout_quieter`` and ``stderr_quieter`` are the same thing as ``quieter``,
  except they are for whether or not the output of the command will be shown.

- ``input`` is a string to be sent to the command's standard input.

- ``stdin`` is ignored if ``input`` is truthy; otherwise, it will be the ``stdin``
  argument passed to ``subprocess.Popen``.

- ``stdout`` and ``stderr`` are passed to ``subprocess.Popen``.

- ``timeout`` is the maximum number of seconds to wait for the command to finish
  before killing it. If you pass a falsy value, it will never kill the command.

- ``env`` is a dictionary of environment variables to pass to the function; if
  ``None``, then the current environment in ``os.environ`` will be passed.

- ``runtime_libpaths`` is a list of strings to be added to the platform's DLL/
  shared library search path.

- ``ignore_error`` will determine whether or not an ``fbuild.ExecutionError`` is
  thrown if the command fails.

- ``kwargs`` is just passed on to ``subprocess.Popen``.

TODO
****

Document ``fbuild.config``, ``Record``, ``pre_options``, and
``ctx.db.add_external_dependencies_to_call``. And ``ctx.install``!
