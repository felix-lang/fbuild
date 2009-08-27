import fbuild.builders
import fbuild.db

# ------------------------------------------------------------------------------

class LlvmConfig(fbuild.db.PersistentObject):
    def __init__(self, ctx, exe='llvm-config',
            requires_version=None,
            requires_at_least_version=None,
            requires_at_most_version=None):
        super().__init__(ctx)

        self.exe = fbuild.builders.find_program(ctx, [exe])

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

    def version(self):
        """Return the version of the llvm-config executable."""
        stdout, stderr = self.ctx.execute([self.exe, '--version'], quieter=1)
        return stdout.decode().strip()

    def __str__(self):
        return self.exe.name
