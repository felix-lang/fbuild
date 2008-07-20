from fbuild import Path, execute
import fbuild.builders

# -----------------------------------------------------------------------------

class Linker:
    def __init__(self, ar, ranlib, flags, *, prefix, suffix):
        self.ar = ar
        self.ranlib = ranlib
        self.flags = flags
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, dst, srcs, *,
            flags=[],
            ranlib_flags=[],
            destdir=None,
            **kwargs):
        dst = dst.parent / self.prefix + dst.name + self.suffix
        srcs = Path.glob_all(srcs)

        assert srcs, 'no sources passed into ar'

        if destdir is not None:
            destdir.make_dirs()
            dst = destdir / dst

        cmd = [self.ar]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)

        execute(cmd,
            msg1=self.ar,
            msg2='%s -> %s' % (' '.join(srcs), dst),
            color='cyan',
            **kwargs)

        if self.ranlib is not None:
            cmd = [self.ranlib]
            cmd.extend(ranlib_flags)
            cmd.append(dst)

            execute(cmd,
                msg1=self.ranlib,
                msg2=dst,
                color='cyan',
                **kwargs)

        return dst

# -----------------------------------------------------------------------------

def make_linker(ar=None, ranlib=None, *,
        prefix='lib',
        suffix='.a',
        link_flags=['-rc'],
        **kwargs):
    ar = ar or fbuild.builders.find_program(['ar'])

    if not ar:
        raise ConfigFailed('cannot find ar')

    ranlib = ranlib or fbuild.builders.find_program(['ranlib'])

    return Linker(ar, ranlib, link_flags,
        prefix=prefix,
        suffix=suffix,
        **kwargs)

# -----------------------------------------------------------------------------

def config(conf, *args, **kwargs):
    try:
        return conf['ar']
    except KeyError:
        ar = conf['ar'] = make_linker(*args, **kwargs)
        return ar
