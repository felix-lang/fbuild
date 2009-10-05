from itertools import chain

import fbuild.db
import fbuild.path

# ------------------------------------------------------------------------------

class SDLConfig(fbuild.db.PersistentObject):
    def __init__(self, ctx, exe=None, *,
            requires_version=None,
            requires_at_least_version=None,
            requires_at_most_version=None):
        super().__init__(ctx)

        self.exe = fbuild.builders.find_program(ctx, [exe or 'sdl-config'])

        # ----------------------------------------------------------------------
        # Check the builder version.

        if any(v is not None for v in (
                requires_version,
                requires_at_least_version,
                requires_at_most_version)):
            self.ctx.logger.check('checking %s version' % str(self))

            version_str = self.version()

            # Convert the version into a tuple
            version = []
            for i in version_str.split('.'):
                try:
                    version.append(int(i))
                except ValueError:
                    # The subversion isn't a number, so just convert it to a
                    # string.
                    version.append(i)
            version = tuple(version)

            if requires_version is not None and requires_version != version:
                raise fbuild.ConfigFailed('version %s required; found %s' %
                    ('.'.join(str(i) for i in requires_version), version_str))

            if requires_at_least_version is not None and \
                    requires_at_least_version > version:
                raise fbuild.ConfigFailed('at least version %s required; '
                    'found %s' % ('.'.join(str(i)
                        for i in requires_at_least_version),
                    version_str))

            if requires_at_most_version is not None and \
                    requires_at_most_version < version:
                raise fbuild.ConfigFailed('at most version %s required; '
                    'found %s' % ('.'.join(str(i)
                        for i in requires_at_most_version),
                    version_str))

            self.ctx.logger.passed(version_str)

    def __call__(self, cmd, *args,  **kwargs):
        stdout, stderr = self.ctx.execute(list(chain((self.exe,), cmd)),
            quieter=1)
        return stdout.decode().strip()

    def version(self, *args, **kwargs):
        return self(('--version',), *args, **kwargs)

    def prefix(self, *args, **kwargs):
        return fbuild.path.Path(self(('--prefix',), *args, **kwargs))

    def exec_prefix(self, *args, **kwargs):
        return fbuild.path.Path(self(('--exec-prefix',), *args, **kwargs))

    def cflags(self, *args, **kwargs):
        return self(('--cflags',), *args, **kwargs)

    def libs(self, *args, **kwargs):
        return self(('--libs',), *args, **kwargs)

    def static_libs(self, *args, **kwargs):
        return self(('--static-libs',), *args, **kwargs)

    def __str__(self):
        return self.exe.name
