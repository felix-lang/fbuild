"""errno.h is a nonstandardized but common header that implements
extensions to the C header."""

import fbuild.config.c as c
import fbuild.config.c.posix04 as posix04

class errno_h(posix04.errno_h):
    error_t = c.type_test()
