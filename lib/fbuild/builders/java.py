from itertools import chain

import fbuild
import fbuild.builders
import fbuild.db
from fbuild.path import Path

# ------------------------------------------------------------------------------

class Jar(fbuild.db.PersistentObject):
    def __init__(self, exe='jar'):
        self.exe = fbuild.builders.find_program([exe])

    # --------------------------------------------------------------------------

    @fbuild.db.cachemethod
    def create(self, dst, srcs:fbuild.db.SRCS, *args,
            manifest:fbuild.db.OPTIONAL_SRC=None,
            **kwargs) -> fbuild.db.DST:
        """Collect all the L{srcs} into a jar and cache the result."""
        return self.uncached_create(dst, srcs, *args,
            manifest=manifest,
            **kwargs)

    def uncached_create(self, dst, srcs, *,
            manifest=None,
            cwd=None,
            buildroot=None,
            **kwargs):
        """Collect all the L{srcs} into a jar."""
        # Unfortunately, we need to adjust the current working directory to
        # where we want the jar files to be relative to. By default we'll at
        # least run jar from the buildroot.

        buildroot = buildroot or fbuild.buildroot
        cwd = cwd or buildroot
        dst = Path(dst).addroot(buildroot)

        # We need ot make sure jars have sources passed in
        assert srcs, "%s: no sources passed in" % dst

        cmd = [self.exe]

        if manifest is None:
            cmd.append('cf')
        else:
            # Adjust the manifest to the cwd.
            cmd.extend(('cmf', Path(manifest).relpath(cwd)))

        # Adjust the dst and srcs to the cwd
        cmd.append(dst.relpath(cwd))
        cmd.extend(Path(src).relpath(cwd) for src in srcs)

        if manifest is None:
            msg2 = '%s -> %s' % (' '.join(srcs), dst)
        else:
            msg2 = '%s %s -> %s' % (manifest, ' '.join(srcs), dst)

        fbuild.execute(cmd, self, msg2, cwd=cwd, color='cyan', **kwargs)

        return dst

    # --------------------------------------------------------------------------

    def __str__(self):
        return self.exe.name

# ------------------------------------------------------------------------------

class Java:
    def __init__(self, exe='java', *, classpaths=[]):
        self.exe = fbuild.builders.find_program([exe])
        self.classpaths = classpaths

    def run_class(self, cls, *args, classpaths=[], **kwargs):
        cmd = [self.exe]

        cmd.extend(('-cp', ':'.join(chain(self.classpaths, classpaths))))
        cmd.append(cls)

        return fbuild.execute(cmd, *args, **kwargs)

    def run_jar(self, jar, *args, **kwargs):
        cmd = [self.exe]
        cmd.extend(('-jar', jar))

        return fbuild.execute(cmd, *args, **kwargs)

    def __str__(self):
        return self.exe.name
