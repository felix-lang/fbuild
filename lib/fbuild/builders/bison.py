from fbuild import buildroot, execute
from fbuild.builders import find_program
from fbuild.path import Path

# -----------------------------------------------------------------------------

class Bison:
    def __init__(self, exe, flags=[], *, suffix='.c'):
        self.exe = exe
        self.flags = flags
        self.suffix = suffix

    def __call__(self, src, dst=None, *,
            suffix=None,
            verbose=False,
            name_prefix=None,
            defines=False,
            flags=[],
            buildroot=buildroot):
        suffix = suffix or self.suffix
        dst = Path.replace_root(dst or src, buildroot).replace_ext(suffix)

        if not dst.is_dirty(src):
            return dst

        dst.parent.make_dirs()

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

        execute(cmd, self.exe, '%s -> %s' % (src, dst), color='yellow')

        return dst

def config(exe=None, default_exes=['bison'], **kwargs):
    exe = exe or find_program(default_exes)

    return Bison(exe, **kwargs)
