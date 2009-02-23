import abc
from functools import partial
from itertools import chain

import fbuild
import fbuild.db
import fbuild.temp
import fbuild.builders
import fbuild.builders.platform
import fbuild.functools
from fbuild.path import Path

# ------------------------------------------------------------------------------

class MissingHeader(fbuild.ConfigFailed):
    def __init__(self, filename=None):
        self.filename = filename

    def __str__(self):
        if self.filename is None:
            return 'missing header'
        else:
            return 'missing header %r' % self.filename

# ------------------------------------------------------------------------------

class Builder(fbuild.builders.AbstractCompilerBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ----------------------------------------------------------------------
        # Check the builder to make sure it works.

        fbuild.logger.check('checking if %s can make objects' % self)
        try:
            with self.tempfile_compile('int main() { return 0; }'):
                fbuild.logger.passed()
        except fbuild.ExecutionError as e:
            raise fbuild.ConfigFailed('compiler failed: %s' % e)

        fbuild.logger.check('checking if %s can make libraries' % self)
        try:
            with self.tempfile_link_lib('int foo() { return 5; }'):
                fbuild.logger.passed()
        except fbuild.ExecutionError as e:
            raise fbuild.ConfigFailed('lib linker failed: %s' % e)

        fbuild.logger.check('checking if %s can make exes' % self)
        try:
            self.tempfile_run('int main() { return 0; }')
        except fbuild.ExecutionError as e:
            raise fbuild.ConfigFailed('exe linker failed: %s' % e)
        else:
            fbuild.logger.passed()

        fbuild.logger.check('checking if %s can link lib to exe' % self)
        with fbuild.temp.tempdir() as dirname:
            src_lib = dirname / 'templib' + self.src_suffix
            with open(src_lib, 'w') as f:
                print('''
                    #ifdef __cplusplus
                    extern "C"
                    #endif
                    int foo() { return 5; }
                ''', file=f)

            src_exe = dirname / 'tempexe' + self.src_suffix
            with open(src_exe, 'w') as f:
                print('''
                    #include <stdio.h>
                    #ifdef __cplusplus
                    extern "C"
                    #endif
                    extern int foo();
                    int main(int argc, char** argv) {
                        printf("%d", foo());
                        return 0;
                    }''', file=f)

            obj = self.uncached_compile(src_lib, quieter=1)
            lib = self.uncached_link_lib(dirname / 'temp', [obj],
                    exports=['foo'],
                    quieter=1)
            obj = self.uncached_compile(src_exe, quieter=1)
            exe = self.uncached_link_exe(dirname / 'temp', [obj],
                    libs=[lib],
                    quieter=1)

            try:
                stdout, stderr = fbuild.execute([exe], quieter=1)
            except ExecutionError:
                raise fbuild.ConfigFailed('failed to link lib to exe')
            else:
                if stdout != b'5':
                    raise fbuild.ConfigFailed('failed to link lib to exe')
                fbuild.logger.passed()

    @fbuild.db.cachemethod
    def build_objects(self, srcs:fbuild.db.SRCS, **kwargs) -> fbuild.db.DSTS:
        """Compile all of the passed in L{srcs} in parallel."""
        # When a object has extra external dependencies, such as .c files
        # depending on .h changes, depending on library changes, we need to add
        # the dependencies in build_objects.  Unfortunately, the db doesn't
        # know about these new files and so it can't tell when a function
        # really needs to be rerun.  So, we'll just not cache this function.
        # We need to add extra dependencies to our call.
        objs = []
        src_deps = []
        dst_deps = []
        for o, s, d in fbuild.scheduler.map(
                partial(self.compile.call, **kwargs),
                srcs):
            objs.append(o)
            src_deps.extend(s)
            dst_deps.extend(d)

        fbuild.db.add_external_dependencies_to_call(
            srcs=src_deps,
            dsts=dst_deps)

        return objs

    @fbuild.db.cachemethod
    def link_lib(self, dst, srcs:fbuild.db.SRCS, *args,
            libs:fbuild.db.SRCS=(),
            **kwargs) -> fbuild.db.DST:
        """Link compiled c files into a library and caches the results."""
        return self.uncached_link_lib(dst, srcs, *args, libs=libs, **kwargs)

    @fbuild.db.cachemethod
    def link_exe(self, dst, srcs:fbuild.db.SRCS, *args,
            libs:fbuild.db.SRCS=(),
            **kwargs) -> fbuild.db.DST:
        """Link compiled c files into an executable without caching the
        results.  This is needed when linking temporary files."""
        return self.uncached_link_exe(dst, srcs, *args, libs=libs, **kwargs)

    # --------------------------------------------------------------------------

    def build_lib(self, dst, srcs, *args, **kwargs):
        """Compile all of the passed in L{srcs} in parallel, then link them
        into a library."""
        return self._build_link(self.link_lib, dst, srcs, *args, **kwargs)

    def build_exe(self, dst, srcs, *args, **kwargs):
        """Compile all of the passed in L{srcs} in parallel, then link them
        into an executable."""
        return self._build_link(self.link_exe, dst, srcs, *args, **kwargs)

    def _build_link(self, function, dst, srcs, *,
            includes=[],
            macros=[],
            warnings=[],
            cflags=[],
            ckwargs={},
            libs=[],
            external_libs=[],
            exports=[],
            lflags=[],
            lkwargs={}):
        """Actually compile and link the sources."""
        objs = self.build_objects(srcs,
            includes=includes,
            macros=macros,
            warnings=warnings,
            flags=cflags,
            **ckwargs)

        return function(dst, objs,
            libs=libs,
            external_libs=external_libs,
            exports=exports,
            flags=lflags,
            **lkwargs)

    # -------------------------------------------------------------------------

    def check_statement(self, name, statement, *,
            msg=None, headers=[], **kwargs):
        code = '''
            %s;
            int main() {
                %s
                return 0;
            }
        ''' % ('\n'.join('#include <%s>' % h for h in headers), statement)

        fbuild.logger.check(msg or 'checking %r' % name)
        if self.try_compile(code, **kwargs):
            fbuild.logger.passed()
            return True
        else:
            fbuild.logger.failed()
            return False

    def check_statements(self, *items, msg='checking %r', **kwargs):
        results = set()
        for name, statement in items:
            if self.check_statement(name, statement, msg=msg % name, **kwargs):
                results.add(name)

        return results

    # -------------------------------------------------------------------------

    def check_header_exists(self, header, **kwargs):
        return self.check_statement(header, '',
            msg='checking if header %r exists' % header,
            headers=[header],
            **kwargs)

    def check_functions_exist(self, *args, **kwargs):
        return self.check_statements(*args,
            msg='checking if function %r exists', **kwargs)

    def check_macros_exist(self, *macros, **kwargs):
        code = '''
            #ifndef %s
            #error %s
            #endif
        '''

        return self.check_statements(
            *((m, code % (m, m)) for m in macros),
            msg='checking if macros %r exists', **kwargs)

    def check_types_exist(self, *types, **kwargs):
        items = []
        for name in types:
            try:
                name, statement = name
            except ValueError:
                name, statement = name, '%s t;' % name
            items.append((name, statement))

        return self.check_statements(*items,
            msg='checking if type %r exists', **kwargs)

# ------------------------------------------------------------------------------

class Library(Path):
    def __new__(cls, *args,
            flags=[],
            libpaths=[],
            libs=[],
            external_libs=[],
            **kwargs):
        self = super().__new__(cls, *args, **kwargs)

        self.flags = flags
        self.libpaths = libpaths
        self.libs = libs
        self.external_libs = external_libs

        return self

    def __repr__(self):
        return 'Library({0}{1}{2}{3}{4})'.format(
            super().__repr__(),
            ', flags={0}'.format(self.flags) if self.flags else '',
            ', libpaths={0}'.format(self.libpaths) if self.libpaths else '',
            ', libs={0}'.format(self.libs) if self.libs else '',
            ', external_libs={0}'.format(self.external_libs)
                if self.external_libs else '')

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return type(self) == type(other) and \
            super().__eq__(other) and \
            self.libpaths == other.libpaths and \
            self.libs == other.libs and \
            self.external_libs == other.external_libs

# ------------------------------------------------------------------------------

def _guess_builder(name, functions, *args,
        platform=None,
        platform_options=[],
        **kwargs):
    platform = fbuild.builders.platform.platform(platform)

    for subplatform, function in functions:
        if subplatform <= platform:
            for p, kw in platform_options:
                if p <= platform:
                    kwargs.update(kw)
            return fbuild.functools.call(function, *args, **kwargs)

    raise fbuild.ConfigFailed('cannot find a builder for %s' %
        (name, platform))

@fbuild.db.caches
def guess_static(*args, **kwargs):
    """L{static} tries to guess the static system c compiler according to the
    platform. It accepts a I{platform} keyword that overrides the system's
    platform. This can be used to use a non-default compiler. Any extra
    arguments and keywords are passed to the compiler's configuration
    functions."""

    return _guess_builder('c static', (
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.static'),
        ({'posix'}, 'fbuild.builders.c.gcc.static'),
        ({'windows'}, 'fbuild.builders.c.msvc.static'),
    ), *args, **kwargs)

@fbuild.db.caches
def guess_shared(*args, **kwargs):
    """L{shared} tries to guess the shared system c compiler according to the
    platform. It accepts a I{platform} keyword that overrides the system's
    platform. This can be used to use a non-default compiler. Any extra
    arguments and keywords are passed to the compiler's configuration
    functions."""

    return _guess_builder('c shared', (
        ({'darwin'}, 'fbuild.builders.c.gcc.darwin.shared'),
        ({'posix'}, 'fbuild.builders.c.gcc.shared'),
        ({'windows'}, 'fbuild.builders.c.msvc.shared'),
    ), *args, **kwargs)

# ------------------------------------------------------------------------------

@fbuild.db.caches
def config_little_endian(builder):
    code = '''
        #include <stdio.h>

        enum enum_t {e_tag};
        typedef void (*fp_t)(void);

        union endian_t {
            unsigned long x;
            unsigned char y[sizeof(unsigned long)];
        } endian;

        int main(int argc, char** argv) {
            endian.x = 1ul;
            printf("%d\\n", endian.y[0]);
            return 0;
        }
    '''

    fbuild.logger.check('checking if little endian')
    try:
        stdout = 1 == int(builder.tempfile_run(code)[0])
    except fbuild.ExecutionError:
        fbuild.logger.failed()
        raise fbuild.ConfigFailed('failed to detect endianness')

    little_endian = int(stdout) == 1
    fbuild.logger.passed(little_endian)

    return little_endian
