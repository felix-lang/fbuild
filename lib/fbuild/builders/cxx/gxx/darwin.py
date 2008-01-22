from ...c.gcc import darwin
from .. import gxx

# -----------------------------------------------------------------------------

def config(conf, exe, make_shared=darwin.make_shared, **kwargs):
    return gxx.config(conf, exe, make_shared=make_shared, **kwargs)
