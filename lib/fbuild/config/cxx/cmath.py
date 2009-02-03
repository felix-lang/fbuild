"""This module extends the C++ 2003 cmath header with common extensions."""

import fbuild.config.c.stdlib
import fbuild.config.cxx.cxx03 as cxx03

# ------------------------------------------------------------------------------

class cmath(cxx03.cmath, fbuild.config.c.stdlib.math_h):
    pass
