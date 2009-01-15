"""This module extends the C++ 2003 cmath header with common extensions."""

import fbuild.config.c.math_h
import fbuild.config.cxx.cxx03 as cxx03

# ------------------------------------------------------------------------------

class cmath(cxx03.cmath, fbuild.config.c.math_h.math_h):
    pass
