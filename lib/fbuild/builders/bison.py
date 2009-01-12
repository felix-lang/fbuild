import fbuild
import fbuild.builders
import fbuild.db
from fbuild.path import Path

# ------------------------------------------------------------------------------

class Bison(fbuild.db.PersistentObject):
    def __init__(self, exe=None, flags=[], *, suffix='.c'):
        self.exe = fbuild.builders.find_program([exe or 'bison'])
        self.flags = flags
        self.suffix = suffix

    def __call__(self, src, dst=None, *,
            suffix=None,
            verbose=False,
            name_prefix=None,
            defines=False,
            flags=[],
            buildroot=None):
        buildroot = buildroot or fbuild.buildroot
        suffix = suffix or self.suffix
        dst = Path.addroot(dst or src, buildroot).replaceext(suffix)
        dst.parent.makedirs()

        cmd = [self.exe]

        if verbose:
            cmd.append('-v')

        if name_prefix is not None:
            cmd.extend(('-p', name_prefix))

        if defines:
            cmd.append('-d')

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(('-o', dst))
        cmd.append(src)

        fbuild.execute(cmd, self.exe, '%s -> %s' % (src, dst), color='yellow')

        return dst
