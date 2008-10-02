from fbuild import ExecutionError, buildroot, env, execute, logger
from fbuild.path import Path
from fbuild.temp import tempfile
from fbuild.builders import AbstractCompilerBuilder, find_program

# -----------------------------------------------------------------------------

class Flx:
    def __init__(self, exe, flags=[]):
        # we split exe in case extra arguments were specified in the name
        self.exe, *self.flags = str.split(exe)
        self.exe = Path(self.exe)
        self.flags.extend(flags)

    def __call__(self, src, *args, includes=[], flags=[], cwd=None, **kwargs):
        cmd = [self.exe]

        cmd.append('--output_dir=' + src.parent)
        cmd.extend('-I' + i for i in sorted(includes) if Path(i).exists())
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(src)

        return execute(cmd, *args, **kwargs)

    def check_flags(self, flags=[]):
        if flags:
            logger.check('checking %s with %s' %
                (self, ' '.join(flags)))
        else:
            logger.check('checking %s' % self)

        with tempfile('', suffix='.flx') as src:
            try:
                self(src, flags=flags, quieter=1)
            except ExecutionError:
                logger.failed()
                return False

        logger.passed()
        return True

    def __str__(self):
        return ' '.join([self.exe] + self.flags)

    def __eq__(self, other):
        return isinstance(other, Flx) and \
            self.exe == other.exe

def config_flx(exe=None, default_exes=['flx'], *, flags=[]):
    exe = exe or find_program(default_exes)

    if not exe:
        raise MissingProgram('exe')

    flx = Flx(exe, flags)

    if not flx.check_flags([]):
        raise ConfigFailed('flx failed to compile an exe')

    return flx

# -----------------------------------------------------------------------------

class Felix(AbstractCompilerBuilder):
    def __init__(self, flx, *, exe_suffix, lib_suffix):
        super().__init__(src_suffix='.flx')

        self.flx = flx
        self.exe_suffix = exe_suffix
        self.lib_suffix = lib_suffix

    def compile(self, src, *,
            static=False,
            flags=[],
            buildroot=buildroot,
            **kwargs):
        src_buildroot = src.replace_root(buildroot)

        if static:
            dst = src_buildroot.replace_ext(self.exe_suffix)
        else:
            dst = src_buildroot.replace_ext(self.lib_suffix)

        if not dst.is_dirty(src):
            return dst

        if src != src_buildroot:
            src_buildroot.parent.make_dirs()
            src.copy(src_buildroot)
            src = src_buildroot

        cmd_flags = ['-c', '--force']
        cmd_flags.extend(flags)

        self.flx(src, self.flx, '%s -> %s' % (src, dst),
            flags=cmd_flags,
            color='green',
            **kwargs)

        return dst

    def run(self, src, *args, **kwargs):
        return self.flx(src.replace_ext(''), *args, **kwargs)

    def __eq__(self, other):
        return isinstance(other, Felix) and \
            self.exe == other.exe and \
            self.exe_suffix == other.exe_suffix

# -----------------------------------------------------------------------------

def config(exe=None, *, flags=[], exe_suffix='', lib_suffix='.dylib', **kwargs):
    flx = env.cache(config_flx, exe, flags=flags)

    return Felix(flx, exe_suffix=exe_suffix, lib_suffix=lib_suffix)
