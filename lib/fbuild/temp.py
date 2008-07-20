import textwrap
import contextlib

from fbuild.path import Path

# -----------------------------------------------------------------------------

@contextlib.contextmanager
def tempdir(*args, **kwargs):
    import tempfile
    path = Path(tempfile.mkdtemp(*args, **kwargs))
    try:
        yield path
    finally:
        path.rmtree()

# -----------------------------------------------------------------------------

@contextlib.contextmanager
def tempfile(src, suffix='', name='temp'):
    with tempdir() as dirname:
        name = dirname / name + suffix
        with open(name, 'w') as f:
            print(textwrap.dedent(src), file=f)

        yield Path(name)
