"""This module extends the posix sys/mman.h header with common extensions."""

import fbuild.config.c.bsd as bsd
import fbuild.config.c.linux as linux

# ------------------------------------------------------------------------------

class sys_mman_h(linux.sys_mman_h, bsd.sys_mman_h):
    pass
