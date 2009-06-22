import io
import re
from itertools import chain

import fbuild
import fbuild.builders
import fbuild.builders.c
import fbuild.builders.platform
from fbuild.path import Path
from fbuild.temp import tempdir, tempfile

# ------------------------------------------------------------------------------

class Cl(fbuild.db.PersistentObject):
    def __init__(self, exe='cl', *,
            pre_flags=[],
            flags=[],
            includes=[],
            macros=[],
            warnings=[],
            debug=None,
            optimize=None,
            debug_flags=['/Zi'],
            optimize_flags=['/Ox']):
        self.exe = fbuild.builders.find_program([exe])
        self.pre_flags = pre_flags
        self.flags = flags
        self.includes = includes
        self.macros = macros
        self.warnings = warnings
        self.debug = debug
        self.optimize = optimize
        self.debug_flags = debug_flags
        self.optimize_flags = optimize_flags

        if not self.check_flags(flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

        if debug_flags and not self.check_flags(debug_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

        if optimize_flags and not self.check_flags(optimize_flags):
            raise fbuild.ConfigFailed('%s failed to compile an exe' % self)

    def __call__(self, srcs, dst=None, *,
            pre_flags=[],
            flags=[],
            includes=[],
            macros=[],
            warnings=[],
            debug=None,
            optimize=None,
            **kwargs):
        new_includes = []
        for include in chain(self.includes, includes, (s.parent for s in srcs)):
            if include not in new_includes:
                new_includes.append(include)
        includes = new_includes

        new_flags = []
        for flag in chain(self.flags, flags):
            if flag not in new_flags:
                new_flags.append(flag)
        flags = new_flags

        macros = set(macros)
        macros.update(self.macros)

        warnings = set(warnings)
        warnings.update(self.warnings)

        # ----------------------------------------------------------------------

        cmd = [self.exe, '/nologo']
        cmd.extend(self.pre_flags)
        cmd.extend(pre_flags)

        if (debug is None and self.debug) or debug:
            cmd.extend(self.debug_flags)

        if (optimize is None and self.optimize) or optimize:
            cmd.extend(self.optimize_flags)

        # make sure that the path is converted into the native path format
        cmd.extend('/I' + Path(i) for i in sorted(includes) if i)
        cmd.extend('/D' + d for d in sorted(macros))
        cmd.extend('/W' + w for w in sorted(warnings))

        if dst is not None:
            cmd.append('/Fo' + dst)
            msg2 = '%s -> %s' % (' '.join(srcs), dst)
        else:
            msg2 = ' '.join(srcs)

        cmd.extend(flags)
        cmd.extend(srcs)

        return fbuild.execute(cmd, msg2=msg2, **kwargs)

    def check_flags(self, flags):
        if flags:
            fbuild.logger.check('checking %s with %s' % (self, ' '.join(flags)))
        else:
            fbuild.logger.check('checking %s' % self)

        code = 'int main(int argc, char** argv){return 0;}'

        with fbuild.temp.tempfile(code, suffix='.c') as src:
            try:
                self([src], flags=flags, quieter=1, cwd=src.parent)
            except fbuild.ExecutionError:
                fbuild.logger.failed()
                return False

        fbuild.logger.passed()
        return True

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.exe.name,), self.flags))

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            self.exe == other.exe and \
            self.flags == other.flags and \
            self.includes == other.includes and \
            self.macros == other.macros and \
            self.warnings == other.warnings and \
            self.debug == other.debug and \
            self.optimize == other.optimize and \
            self.debug_flags == other.debug_flags and \
            self.optimize_flags == other.optimize_flags

    def __hash__(self):
        return hash((
            self.exe,
            self.pre_flags,
            self.flags,
            self.includes,
            self.macros,
            self.warnings,
            self.debug,
            self.optimize,
            self.debug_flags,
            self.optimize_flags,
        ))

# ------------------------------------------------------------------------------

class Compiler:
    def __init__(self, cl, flags, *, suffix):
        self.cl = cl
        self.flags = flags
        self.suffix = suffix

    def __call__(self, src, dst=None, *,
            suffix=None,
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        src = Path(src)

        suffix = suffix or self.suffix
        dst = (dst or src).addroot(buildroot).replaceext(suffix)
        dst.parent.makedirs()

        stdout, stderr = self.cl([src], dst,
            pre_flags=list(chain(['/c'], self.flags)),
            msg1=str(self),
            color='green',
            **kwargs)

        return dst, stdout, stderr

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.cl,), self.flags))

    def __eq__(self, other):
        return isinstance(other, Compiler) and \
            self.cl == other.cl and \
            self.flags == other.flags and \
            self.suffix == other.suffix

    def __hash__(self):
        return hash((self.cl, self.flags, self.suffix))

# ------------------------------------------------------------------------------

class Lib(fbuild.db.PersistentObject):
    def __init__(self, exe='lib', *,
            pre_flags=[],
            flags=[],
            libpaths=[],
            libs=[],
            external_libs=[]):
        self.exe = fbuild.builders.find_program([exe])
        self.pre_flags = pre_flags
        self.flags = flags
        self.libpaths = libpaths
        self.libs = libs
        self.external_libs = external_libs

    def __call__(self, dst, srcs, *,
            pre_flags=[],
            flags=[],
            libpaths=[],
            libs=[],
            external_libs=[],
            buildroot=None,
            **kwargs):
        buildroot = buildroot or fbuild.buildroot
        dst = Path(dst).addroot(buildroot)
        dst = dst.parent / dst.name + '.lib'
        dst.parent.makedirs()

        cmd = [self.exe, '/nologo']
        cmd.extend(self.pre_flags)
        cmd.extend(pre_flags)
        cmd.append('/OUT:' + dst)
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend(srcs)

        # We'll ignore linking libraries to libraries for now.
        #cmd.extend('/DEFAULTLIB:' + l for l in self.external_libs)
        #cmd.extend('/DEFAULTLIB:' + l for l in external_libs)
        #for lib in chain(self.libs, libs):
        #    if lib.endswith('.dll'):
        #        cmd.append(lib[:-4] + '.lib')
        #    else:
        #        cmd.append(lib)

        fbuild.execute(cmd, str(self),
            '%s -> %s' % (' '.join(chain(srcs, libs)), dst),
            color='cyan',
            **kwargs)

        return dst

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.exe.name,), self.flags))

# ------------------------------------------------------------------------------

class Link(fbuild.db.PersistentObject):
    def __init__(self, exe='link', *,
            pre_flags=[],
            flags=[],
            libpaths=[],
            libs=[],
            external_libs=[]):
        self.exe = fbuild.builders.find_program([exe])
        self.pre_flags = pre_flags
        self.flags = flags
        self.libpaths = libpaths
        self.libs = libs
        self.external_libs = external_libs

    def _run(self, dst, srcs, *,
            pre_flags=[],
            flags=[],
            libpaths=[],
            libs=[],
            external_libs=[],
            buildroot=None,
            **kwargs):
        new_libpaths = []
        for libpath in chain(self.libpaths, libpaths):
            if libpath not in new_libpaths:
                new_libpaths.append(libpath)
        libpaths = new_libpaths

        new_external_libs = []
        for lib in chain(self.external_libs, external_libs):
            if lib not in new_external_libs:
                new_external_libs.append(lib)
        external_libs = new_external_libs

        # Since the libs could be derived from fbuild.builders.c.Library, we need
        # to extract the extra libs and flags that they need.  Linux needs the
        # libraries listed in a particular order.  Libraries must appear left
        # of their dependencies in order to optimize linking.
        new_libs = []
        def f(lib):
            if lib in new_libs:
                return

            if isinstance(lib, fbuild.builders.c.Library):
                for flag in lib.flags:
                    if flag not in flags:
                        flags.append(flag)

                for libpath in lib.libpaths:
                    if libpath not in libpaths:
                        libpaths.append(libpath)

                for l in lib.external_libs:
                    if l not in external_libs:
                        external_libs.append(l)

                # In order to make linux happy, we'll recursively walk the
                # dependencies first, then add the library.
                for l in lib.libs:
                    f(l)

            new_libs.append(lib)

        for lib in chain(self.libs, libs):
            f(lib)

        # Finally, we need to reverse the list so it's in the proper order.
        new_libs.reverse()
        libs = new_libs

        # ----------------------------------------------------------------------

        cmd = [self.exe, '/nologo']
        cmd.extend(self.pre_flags)
        cmd.extend(pre_flags)
        cmd.append('/OUT:' + dst)
        cmd.extend(self.flags)
        cmd.extend(flags)
        cmd.extend('/LIBRARYPATH:' + p for p in sorted(libpaths) if p)

        for lib in chain(self.external_libs, external_libs, self.libs, libs):
            if lib.endswith('.dll'):
                cmd.append('/DEFAULTLIB:' + lib[:-4] + '.lib')
            else:
                cmd.append('/DEFAULTLIB:' + lib)

        cmd.extend(srcs)

        stdout, stderr = fbuild.execute(cmd, str(self),
            '%s -> %s' % (' '.join(chain(srcs, libs)), dst),
            color='cyan',
            **kwargs)

        return dst, stdout, stderr

    def _make_dst(self, dst, suffix, buildroot):
        dst = Path(dst).addroot(buildroot or fbuild.buildroot)
        dst = dst.parent / dst.name + suffix
        dst.parent.makedirs()

        return dst

    def __str__(self):
        return ' '.join(str(s) for s in chain((self.exe.name,), self.flags))

class ExeLink(Link):
    def __call__(self, dst, *args, buildroot=None, **kwargs):
        obj, stdout, stderr = self._run(
            self._make_dst(dst, '.exe', buildroot),
            *args, **kwargs)

        return obj

class DllLink(Link):
    def __call__(self, dst, *args,
            buildroot=None,
            flags=[],
            quieter=0,
            stdout_quieter=0,
            **kwargs):
        obj, stdout, stderr = self._run(
            self._make_dst(dst, '.dll', buildroot),
            flags=list(chain(flags, ['/DLL'])),
            quieter=quieter,
            stdout_quieter=1 if stdout_quieter == 0 else stdout_quieter,
            *args, **kwargs)

        lib = self._make_dst(dst, '.lib', buildroot)
        exp = self._make_dst(dst, '.exp', buildroot)

        # Filter out the message link.exe says when it's linking
        msg = '   Creating library %s and object %s\r\n' % (lib, exp)
        for line in io.StringIO(stdout.decode()):
            if line != msg:
                fbuild.logger.write(line)

        return obj

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.c.Builder):
    def __init__(self, *args,
            compiler,
            lib_linker,
            exe_linker,
            **kwargs):
        self.compiler = compiler
        self.lib_linker = lib_linker
        self.exe_linker = exe_linker

        # This needs to come last as the parent class tests the builder.
        super().__init__(*args, **kwargs)

    def __str__(self):
        return str(self.compiler)

    # --------------------------------------------------------------------------

    _dep_regex = re.compile(r'^Note: +including file: +(.*)\r\n')

    @fbuild.db.cachemethod
    def compile(self, src:fbuild.db.SRC, dst=None, *,
            flags=[],
            quieter=0,
            stdout_quieter=0,
            **kwargs) -> fbuild.db.DST:
        """Compile a c file and cache the results."""
        src = Path(src)

        # Generate the dependencies while we compile the file.
        try:
            obj, stdout, stderr = self.compiler(src, dst,
                flags=list(chain(('/showIncludes',), flags)),
                quieter=quieter,
                stdout_quieter=1 if stdout_quieter == 0 else stdout_quieter,
                **kwargs)
        except fbuild.ExecutionError as e:
            if quieter == 0 and stdout_quieter == 0:
                # We errored out, but we've hidden the stdout output.
                # Display the output while filtering out the dependeny
                # info.
                for line in io.StringIO(e.stdout.decode()):
                    if not self._dep_regex.match(line) and \
                            line != src.name.splitext()[0] + '\r\n':
                        fbuild.logger.write(line)
            raise e

        # Parse the output and return the module dependencies.
        deps = []
        for line in io.StringIO(stdout.decode()):
            m = self._dep_regex.match(line)
            if m:
                # The path sometimes is absolute, so try to convert it into a
                # relative path.
                try:
                    deps.append(Path(m.group(1)).relpath())
                except ValueError:
                    # We couldn't find a relative path, so it must be from
                    # outside our project.  Lets just ignore that dependency
                    # for now.
                    pass
            elif quieter == 0 and stdout_quieter == 0:
                if line != src.name + '\r\n':
                    fbuild.logger.write(line)

        fbuild.db.add_external_dependencies_to_call(srcs=deps)

        return obj

    def uncached_compile(self, *args, **kwargs):
        """Compile a c file without caching the results.  This is needed when
        compiling temporary files."""
        dst, stdout, stderr = self.compiler(*args, **kwargs)
        return dst

    def uncached_link_lib(self, *args, **kwargs):
        """Link compiled c files into a library without caching the results.
        This is needed when linking temporary files."""
        lib = self.lib_linker(*args, **kwargs)
        return fbuild.builders.c.Library(lib,
            flags=kwargs.get('flags', []),
            libpaths=kwargs.get('libpaths', []),
            libs=kwargs.get('libs', []),
            external_libs=kwargs.get('external_libs', []))

    def uncached_link_exe(self, *args, **kwargs):
        """Link compiled c files into am executable without caching the
        results.  This is needed when linking temporary files."""
        return self.exe_linker(*args, **kwargs)

    # --------------------------------------------------------------------------

    def __repr__(self):
        return '%s(compiler=%r, lib_linker=%r, exe_linker=%r)' % (
            self.__class__.__name__,
            self.compiler,
            self.lib_linker,
            self.exe_linker)

    def __eq__(self, other):
        return isinstance(other, Builder) and \
                self.compiler == other.compiler and \
                self.lib_linker == other.lib_linker and \
                self.exe_linker == other.exe_linker

    def __hash__(self):
        return hash((
            self.compiler,
            self.lib_linker,
            self.exe_linker,
        ))

# ------------------------------------------------------------------------------

def static(exe=None, *args,
        platform=None,
        flags=[],
        compile_flags=[],
        libpaths=[],
        libs=[],
        link_flags=[],
        lib_link_flags=[],
        exe_link_flags=[],
        src_suffix='.c',
        **kwargs):
    return Builder(
        compiler=Compiler(Cl(**kwargs),
            flags=list(chain(flags, compile_flags)),
            suffix=fbuild.builders.platform.static_obj_suffix(platform)),
        lib_linker=Lib(
            pre_flags=list(chain(link_flags, lib_link_flags)),
            libs=libs,
            libpaths=libpaths),
        exe_linker=ExeLink(
            pre_flags=list(chain(link_flags, exe_link_flags))),
        src_suffix=src_suffix,
        flags=flags)

# ------------------------------------------------------------------------------

def shared(exe=None, *args,
        platform=None,
        flags=[],
        compile_flags=[],
        libpaths=[],
        libs=[],
        link_flags=[],
        lib_link_flags=[],
        exe_link_flags=[],
        src_suffix='.c',
        **kwargs):
    return Builder(
        compiler=Compiler(Cl(**kwargs),
            flags=list(chain(flags, compile_flags)),
            suffix=fbuild.builders.platform.shared_obj_suffix(platform)),
        lib_linker=DllLink(
            pre_flags=list(chain(link_flags, lib_link_flags))),
        exe_linker=ExeLink(
            pre_flags=list(chain(link_flags, exe_link_flags))),
        src_suffix=src_suffix,
        flags=flags)
