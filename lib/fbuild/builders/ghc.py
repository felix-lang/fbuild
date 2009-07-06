from functools import partial
from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.platform
import fbuild.db
import fbuild.path
import fbuild.temp

# ------------------------------------------------------------------------------

class Ghc(fbuild.db.PersistentObject):
    """Create a ghc driver."""

    def __init__(self, exe, *, flags=[]):
        self.exe = fbuild.builders.find_program([exe if exe else 'ghc'])
        self.flags = flags

        if not self.check_flags(flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

    def __call__(self, dst, srcs, *,
            pre_flags=[],
            flags=[],
            odir=None,
            hidir=None,
            **kwargs):
        cmd = [self.exe]

        cmd.extend(pre_flags)
        cmd.extend(('-o', dst))

        if odir is not None:  cmd.extend(('-odir', odir))
        if hidir is not None: cmd.extend(('-hidir', hidir))

        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(srcs)

        return fbuild.execute(cmd, str(self),
            msg2='%s -> %s' % (' '.join(srcs), dst),
            **kwargs)

    def check_flags(self, flags):
        if flags:
            fbuild.logger.check('checking %s with %s' (self, ' '.join(flags)))
        else:
            fbuild.logger.check('checking %s' % self)

        code = '''
        import System.Exit
        main = exitSuccess
        '''

        with fbuild.temp.tempfile(code, suffix='.hs') as src:
            try:
                self('test', [src], flags=flags, quieter=1, cwd=src.parent)
            except fbuild.ExecutionError:
                fbuild.logger.failed()
                return False

        fbuild.logger.passed()
        return True

    def __str__(self):
        return self.exe.name

    def __eq__(self, other):
        return isinstance(other, Ghc) and \
            self.exe == other.exe and \
            self.flags == other.flags

    def __hash__(self):
        return hash((
            self.exe,
            self.flags,
        ))

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.AbstractExeLinker):
    def __init__(self, *,
            ghc='ghc',
            platform=None,
            **kwargs):
        super().__init__(src_suffix='.hs')

        self.ghc = Ghc(ghc, **kwargs)
        self.obj_suffix = fbuild.builders.platform.obj_suffix(platform)

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, *args, **kwargs) -> fbuild.db.DST:
        """Compile a haskell file and cache the results."""
        return self.uncached_compile(src, *args, **kwargs)

    def uncached_compile(self, src, dst=None, *args,
            pre_flags=[],
            odir=None,
            hidir=None,
            buildroot=None,
            **kwargs):
        """Compile a haskell file."""

        buildroot = buildroot or fbuild.buildroot

        src = fbuild.path.Path(src)
        dst = fbuild.path.Path(dst or src).replaceext(self.obj_suffix)
        dst = dst.addroot(buildroot)

        dst.parent.makedirs()

        pre_flags = list(pre_flags)
        pre_flags.append('-c')

        self.ghc(dst, [src],
            pre_flags=pre_flags,
            odir=fbuild.path.Path(odir or dst.parent),
            hidir=fbuild.path.Path(hidir or dst.parent),
            color='green',
            *args, **kwargs)

        return dst

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def link_exe(self, dst, srcs:fbuild.db.SRCS, *args,
            **kwargs) -> fbuild.db.DST:
        """Link all the L{srcs} into an executable and cache the result."""
        return self.uncached_link_exe(dst, srcs, *args, **kwargs)

    def uncached_link_exe(self, dst, srcs, *args, buildroot=None, **kwargs):
        """Link all the L{srcs} into an executable."""
        dst = fbuild.path.Path(dst).addroot(buildroot or fbuild.buildroot)
        dst.parent.makedirs()

        self.ghc(dst, srcs, *args, color='cyan', **kwargs)

        return dst

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def build_objects(self, srcs:fbuild.db.SRCS,
            **kwargs) -> fbuild.db.DSTS:
        """Compile all the L{srcs} in parallel."""

        return fbuild.scheduler.map(partial(self.compile, **kwargs), srcs)

    def build_exe(self, dst, srcs:fbuild.db.SRCS, *args,
            ckwargs={},
            lkwargs={},
            **kwargs) -> fbuild.db.DST:
        """Compile all the L{srcs} and link into an executable."""
        objs = self.build_objects(srcs, **dict(kwargs, **ckwargs))
        return self.link_exe(dst, objs, **dict(kwargs, **lkwargs))
