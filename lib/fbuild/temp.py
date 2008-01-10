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
def tempfile(*args, **kwargs):
    fd, name = _tempfile.mkstemp(*args, **kwargs)
    try:
        with os.fdopen(fd) as f:
            yield f, name
    finally:
        os.close(fd)
        os.remove(name)
