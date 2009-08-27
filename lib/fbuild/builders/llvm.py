from itertools import chain

import fbuild.builders
import fbuild.db
import fbuild.path

# ------------------------------------------------------------------------------

class LlvmConfig(fbuild.db.PersistentObject):
    def __init__(self, ctx, exe=None, *,
            requires_version=None,
            requires_at_least_version=None,
            requires_at_most_version=None):
        super().__init__(ctx)

        self.exe = fbuild.builders.find_program(ctx, [exe or 'llvm-config'])

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

    def __call__(self, cmd, *args, **kwargs):
        stdout, stderr = self.ctx.execute(list(chain((self.exe,), cmd)), quieter=1)
        return stdout.decode().strip()

    def version(self, *args, **kwargs):
        """Return the version of the llvm-config executable."""
        return self(('--version',), *args, **kwargs)

    def prefix(self, *args, **kwargs):
        """Return the install prefix of the llvm-config executable."""
        return fbuild.path.Path(self(('--prefix',), *args, **kwargs))

    def src_root(self, *args, **kwargs):
        """Return the source root LLVM was built from."""
        return fbuild.path.Path(self(('--src-root',), *args, **kwargs))

    def obj_root(self, *args, **kwargs):
        """Return the object root used to build LLVM."""
        return fbuild.path.Path(self(('--src-root',), *args, **kwargs))

    def bindir(self, *args, **kwargs):
        """Return the directory containing the LLVM executables."""
        return fbuild.path.Path(self(('--bindir',), *args, **kwargs))

    def includedir(self, *args, **kwargs):
        """Return the directory containing the LLVM headers."""
        return fbuild.path.Path(self(('--includedir',), *args, **kwargs))

    def libdir(self, *args, **kwargs):
        """Return the directory containing the LLVM libraries."""
        return fbuild.path.Path(self(('--libdir',), *args, **kwargs))

    def ocaml_libdir(self, *args, **kwargs):
        """Return the directory containing the LLVM O'Caml library bindings."""
        return self.libdir(*args, **kwargs) / 'ocaml'

    def cppflags(self, components=(), *args, **kwargs):
        """Return C preprocessor flags for files that include LLVM headers."""
        return self(tuple(chain(('--cppflags',), components)), *args, **kwargs)

    def cflags(self, components=(), *args, **kwargs):
        """Return C compiler flags for files that include LLVM headers."""
        return self(tuple(chain(('--cflags',), components)), *args, **kwargs)

    def cxxflags(self, components=(), *args, **kwargs):
        """Return C++ compiler flags for files that include LLVM headers."""
        return self(tuple(chain(('--cxxflags',), components)), *args, **kwargs)

    def ldflags(self, components=(), *args, **kwargs):
        """Return linker flags"""
        return self(tuple(chain(('--ldflags',), components)), *args, **kwargs)

    def libs(self, componentes=(), *args, **kwargs):
        """Return library names needed to link against LLVM components."""
        return self(tuple(chain(('--libs',), components)), *args, **kwargs)

    def libnames(self, components=(), *args, **kwargs):
        """Return bare library names for LLVM components."""
        return self(tuple(chain(('--libnames',), components)), *args, **kwargs)

    def libfiles(self, components=(), *args, **kwargs):
        """Return fully qualified library filenames needed to link against LLVM
        components."""
        return self(tuple(chain(('--libfiles',), components)), *args, **kwargs)

    def components(self, *args, **kwargs):
        """Return all the possible components."""
        return self(('--components',), *args, **kwargs)

    def targets_built(self, *args, **kwargs):
        """Return all targets currently built."""
        return self(('--targets-built',), *args, **kwargs)

    def host_target(self, *args, **kwargs):
        """Return target triple used to configure LLVM."""
        return self(('--host-target',), *args, **kwargs)

    def build_mode(self, *args, **kwargs):
        """Return the build mode of LLVM tree."""
        return self(('--build-mode',), *args, **kwargs)

    def __str__(self):
        return self.exe.name
