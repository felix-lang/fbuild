import os
import tempfile as _tempfile
import shutil
import textwrap
import contextlib

# -----------------------------------------------------------------------------

@contextlib.contextmanager
def tempdir(*args, **kwargs):
    name = _tempfile.mkdtemp(*args, **kwargs)
    try:
        yield name
    finally:
        shutil.rmtree(name)

# -----------------------------------------------------------------------------

@contextlib.contextmanager
def tempfile(src, suffix='', name='temp'):
    with tempdir() as dirname:
        name = os.path.join(dirname, name + suffix)
        with open(name, 'w') as f:
            print(textwrap.dedent(src), file=f)

        yield name
