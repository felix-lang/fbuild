import collections
import re

import fbuild
import fbuild.db

# ------------------------------------------------------------------------------

@fbuild.db.caches
def format_substitute(dst, src:fbuild.db.src, patterns, *, buildroot=None) \
        -> fbuild.db.dst:
    """L{format_substitute} replaces the I{patterns} in the file named I{src}
    and saves the changes into file named I{dst}. It uses python's format
    patterns for finding the insertion points."""

    fbuild.logger.log(' * creating ' + dst, color='cyan')

    buildroot = buildroot or fbuild.buildroot
    src = fbuild.path.Path(src)
    dst = fbuild.path.Path.addroot(dst, buildroot)
    dst.parent.makedirs()

    with open(src, 'r') as src_file:
        code = src_file.read().format(**patterns)

    with open(dst, 'w') as dst_file:
        dst_file.write(code)

    return dst

@fbuild.db.caches
def m4_substitute(dst, src:fbuild.db.src, patterns, *, buildroot=None) \
        -> fbuild.db.dst:
    """L{m4_substitute} replaces the I{patterns} in the file named I{src} and
    saves the changes into file named I{dst}. It uses m4-style @word@ patterns
    for find the insertion points."""

    fbuild.logger.log(' * creating ' + dst, color='cyan')

    buildroot = buildroot or fbuild.buildroot
    src = fbuild.path.Path(src)
    dst = fbuild.path.Path.addroot(dst, buildroot)
    dst.parent.makedirs()

    def replace(match):
        value = patterns[match.group(1)]
        if isinstance(value, str):
            return value
        elif isinstance(value, collections.Iterable):
            return ' '.join(str(v) for v in value)
        return str(value)

    with open(src, 'r') as src_file:
        code = re.sub('@(\w+)@', replace, src_file.read(), re.M)

    with open(dst, 'w') as dst_file:
        dst_file.write(code)

    return dst
