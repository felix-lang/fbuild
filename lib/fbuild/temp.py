import contextlib
import tempfile as _tempfile
import textwrap
import os

from fbuild.path import Path

_default_tempdir = None

# ------------------------------------------------------------------------------

def set_default_tempdir(tmp):
    '''
    Set the directory to use as the default temporary directory.
    '''
    global _default_tempdir
    _default_tempdir = Path(tmp).abspath()

# ------------------------------------------------------------------------------

@contextlib.contextmanager
def tempdir(dir=None, *args, **kwargs):
    '''
    Create a temporary directory and yield it's path. When we regain context,
    remove the directory.
    '''

    path = Path(_tempfile.mkdtemp(dir=dir or _default_tempdir, *args, **kwargs))
    try:
        yield path
    finally:
        path.rmtree(ignore_errors=True)

# ------------------------------------------------------------------------------

@contextlib.contextmanager
def tempfile(src='', suffix='', name='temp', **kwargs):
    '''
    Create a temporary file in a unique directory and yield the name of the
    file. When we regain context, remove the directory.

    @param src:    write this source in the tempfile before yielding
    @param suffix: the default suffix of the temp file
    @param name:   the name of the temp file
    '''

    with tempdir(**kwargs) as dirname:
        name = dirname / name + suffix
        with open(name, 'w') as f:
            print(textwrap.dedent(src), file=f)

        yield Path(name)
