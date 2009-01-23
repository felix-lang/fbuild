"""Extend the posix 2004 standard with many common extensions."""

import fbuild.config.c as c
import fbuild.config.c.posix04 as posix04

# ------------------------------------------------------------------------------

class sys_types_h(posix04.sys_types_h):
    header = 'sys/types.h'

    u_int64_t = c.type_test()
