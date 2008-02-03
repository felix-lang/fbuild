import fbuild.builders

# -----------------------------------------------------------------------------

class Linker:
    def __init__(self, system, ar, ranlib, flags, *, prefix, suffix):
        self.system = system
        self.ar = ar
        self.ranlib = ranlib
        self.flags = flags
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, dst, srcs, *, flags=[], ranlib_flags=[], **kwargs):
        dst = fbuild.path.make_path(dst, self.prefix, self.suffix)
        srcs = fbuild.path.glob_paths(srcs)

        cmd = [self.ar]
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.append(dst)
        cmd.extend(srcs)

        self.system.execute(cmd,
            msg1=self.ar,
            msg2='%s -> %s' % (' '.join(srcs), dst),
            color='cyan',
            **kwargs)

        if self.ranlib is not None:
            cmd = [self.ranlib]
            cmd.extend(ranlib_flags)
            cmd.append(dst)

            self.system.execute(cmd,
                msg1=self.ranlib,
                msg2=dst,
                color='cyan',
                **kwargs)

        return dst

# -----------------------------------------------------------------------------

def make_linker(system, ar=None, ranlib=None, *,
        prefix='lib',
        suffix='.a',
        link_flags=['-rc'],
        **kwargs):
    ar = ar or fbuild.builders.find_program(system, ['ar'])

    if not ar:
        raise ConfigFailed('cannot find ar')

    ranlib = ranlib or fbuild.builders.find_program(system, ['ranlib'])

    return Linker(system, ar, ranlib, link_flags,
        prefix=prefix,
        suffix=suffix,
        **kwargs)

# -----------------------------------------------------------------------------

def config(conf, *args, **kwargs):
    try:
        return conf.ar
    except AttributeError:
        conf.ar = make_linker(conf.system, *args, **kwargs)
        return conf.ar
