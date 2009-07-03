from itertools import chain

from fbuild import execute
import fbuild.builders
import fbuild.builders.ocaml as ocaml
import fbuild.db

# ------------------------------------------------------------------------------

class Ocamldep(ocaml.Ocamldep):
    """Overload ocaml.Ocamldep builder to use ocamlfind's ocamldep."""

    def __init__(self, exe=None, *args,
            pre_flags=[],
            packages=[],
            syntaxes=[],
            ppopts=[],
            **kwargs):
        self.packages = packages
        self.syntaxes = syntaxes
        self.ppopts = ppopts

        # We'll use ocamlfind as our executable and add ocamldep as the first
        # preflag.
        exe = fbuild.builders.find_program([exe if exe else 'ocamlfind'])
        super().__init__(exe, *args,
            pre_flags=['ocamldep'] + pre_flags,
            **kwargs)

    def modules(self, *args,
            flags=[],
            packages=[],
            syntaxes=[],
            ppopts=[],
            **kwargs):
        """Calculate the module this ocaml file depends on."""

        # Add the ocamlfind-specific flags to the flags
        flags = list(flags)

        for package in chain(self.packages, packages):
            flags.extend(('-package', package))

        for syntax in chain(self.syntaxes, syntaxes):
            flags.extend(('-syntax', syntax))

        for ppopt in chain(self.ppopts, ppopts):
            flags.extend(('-ppopt', ppopt))

        return super().modules(*args, flags=flags, **kwargs)

    def __str__(self):
        return self.exe.name + ' ocamldep'

# ------------------------------------------------------------------------------

class Ocamlc(ocaml.Ocamlc):
    """Overload ocaml.Ocamlc builder to use ocamlfind's ocamlc."""

    def __init__(self, exe=None, *args,
            pre_flags=[],
            ocamldep=None,
            packages=[],
            syntaxes=[],
            linkpkg=True,
            ppopts=[],
            **kwargs):
        self.packages = packages
        self.syntaxes = syntaxes
        self.linkpkg = linkpkg
        self.ppopts = ppopts

        # We'll use ocamlfind as our executable and add ocamlc as the first
        # preflag.
        exe = fbuild.builders.find_program([exe if exe else 'ocamlfind'])
        super().__init__(exe, *args,
            pre_flags=['ocamlc'] + pre_flags,
            ocamldep=ocamldep if ocamldep else Ocamldep(
                packages=packages,
                syntaxes=syntaxes,
                ppopts=ppopts),
            **kwargs)

    def where(self):
        stdout, stderr = execute([self.exe, 'ocamlc', '-where'], quieter=1)
        return Path(stdout.decode().strip())

    def version(self):
        """Return the version of the ocaml executable."""
        stdout, stderr = execute([self.exe, 'ocamlc', '-version'], quieter=1)
        return stdout.decode().strip()

    def _run(self, *args,
            flags=[],
            packages=[],
            syntaxes=[],
            ppopts=[],
            **kwargs):
        # Add the ocamlfind-specific flags to the flags
        flags = list(flags)

        for package in chain(self.packages, packages):
            flags.extend(('-package', package))

        for syntax in chain(self.syntaxes, syntaxes):
            flags.extend(('-syntax', syntax))

        for ppopt in chain(self.ppopts, ppopts):
            flags.extend(('-ppopt', ppopt))

        return super()._run(*args, flags=flags, **kwargs)

    def build_objects(self, *args,
            packages=[],
            syntaxes=[],
            ppopts=[],
            ocamldep_flags=[],
            **kwargs):

        # Add the ocamlfind-specific flags to the flags
        ocamldep_flags = list(ocamldep_flags)

        for package in chain(self.packages, packages):
            ocamldep_flags.extend(('-package', package))

        for syntax in chain(self.syntaxes, syntaxes):
            ocamldep_flags.extend(('-syntax', syntax))

        for ppopt in chain(self.ppopts, ppopts):
            ocamldep_flags.extend(('-ppopt', ppopt))

        return super().build_objects(*args,
            ocamldep_flags=ocamldep_flags,
            packages=packages,
            syntaxes=syntaxes,
            ppopts=ppopts,
            **kwargs)

    def link_exe(self, *args, flags=[], linkpkg=None, **kwargs):
        """Compile all the L{srcs} and link into an executable."""

        # Add the ocamlfind-specific link flags to the flags
        flags = list(flags)

        linkpkg = self.linkpkg if linkpkg is None else linkpkg
        if linkpkg:
            flags.append('-linkpkg')

        return super().link_exe(*args, flags=flags, **kwargs)

    def __str__(self):
        return self.exe.name + ' ocamlc'

# ------------------------------------------------------------------------------

class Ocamlopt(ocaml.Ocamlopt):
    """Overload ocaml.Ocamlc builder to use ocamlfind's ocamlopt."""

    def __init__(self, exe=None, *args,
            pre_flags=[],
            ocamldep=None,
            ocamlc=None,
            packages=[],
            syntaxes=[],
            linkpkg=True,
            ppopts=[],
            **kwargs):
        self.packages = packages
        self.syntaxes = syntaxes
        self.linkpkg = linkpkg
        self.ppopts = ppopts

        # We'll use ocamlfind as our executable and add ocamlopt as the first
        # preflag.
        exe = fbuild.builders.find_program([exe if exe else 'ocamlfind'])
        ocamldep = ocamldep if ocamldep else Ocamldep(
            packages=packages,
            syntaxes=syntaxes)

        super().__init__(exe, *args,
            pre_flags=['ocamlopt'] + pre_flags,
            ocamldep=ocamldep,
            ocamlc=ocamlc if ocamlc else Ocamlc(
                ocamldep=ocamldep,
                packages=packages,
                syntaxes=syntaxes,
                linkpkg=linkpkg,
                ppopts=ppopts),
            **kwargs)

    def where(self):
        stdout, stderr = execute([self.exe, 'ocamlopt', '-where'], quieter=1)
        return Path(stdout.decode().strip())

    def version(self):
        """Return the version of the ocaml executable."""
        stdout, stderr = execute([self.exe, 'ocamlopt', '-version'], quieter=1)
        return stdout.decode().strip()

    def _run(self, *args,
            flags=[],
            packages=[],
            syntaxes=[],
            ppopts=[],
            **kwargs):
        # Add the ocamlfind-specific flags to the flags
        flags = list(flags)

        for package in chain(self.packages, packages):
            flags.extend(('-package', package))

        for syntax in chain(self.syntaxes, syntaxes):
            flags.extend(('-syntax', syntax))

        for ppopt in chain(self.ppopts, ppopts):
            flags.extend(('-ppopt', ppopt))

        return super()._run(*args, flags=flags, **kwargs)

    def build_objects(self, *args,
            packages=[],
            syntaxes=[],
            ppopts=[],
            ocamldep_flags=[],
            **kwargs):

        # Add the ocamlfind-specific flags to the flags
        ocamldep_flags = list(ocamldep_flags)

        for package in chain(self.packages, packages):
            ocamldep_flags.extend(('-package', package))

        for syntax in chain(self.syntaxes, syntaxes):
            ocamldep_flags.extend(('-syntax', syntax))

        for ppopt in chain(self.ppopts, ppopts):
            flags.extend(('-ppopt', ppopt))

        return super().build_objects(*args,
            ocamldep_flags=ocamldep_flags,
            packages=packages,
            syntaxes=syntaxes,
            ppopts=ppopts,
            **kwargs)

    def link_exe(self, *args, flags=[], linkpkg=None, **kwargs):
        """Compile all the L{srcs} and link into an executable."""

        # Add the ocamlfind-specific link flags to the flags
        flags = list(flags)

        linkpkg = self.linkpkg if linkpkg is None else linkpkg
        if linkpkg:
            flags.append('-linkpkg')

        return super().link_exe(*args, flags=flags, **kwargs)

    def __str__(self):
        return self.exe.name + ' ocamlopt'

# ------------------------------------------------------------------------------

class Ocaml(ocaml.Ocaml):
    """Overload ocaml.Ocaml builder to use ocamlfind."""

    def __init__(self, *, ocamldep=None, ocamlc=None, ocamlopt=None,
            packages=[],
            syntaxes=[],
            ppopts=[],
            **kwargs):
        # We purposefully do not use ocaml.Ocaml's constructor as we want to
        # use ocamlfind's builders.

        self.ocamldep = ocamldep or Ocamldep(
            packages=packages,
            syntaxes=syntaxes,
            ppopts=ppopts)

        self.ocamlc = Ocamlc(
            ocamldep=ocamldep,
            exe=ocamlc,
            packages=packages,
            syntaxes=syntaxes,
            ppopts=ppopts,
            **kwargs)

        self.ocamlopt = Ocamlopt(
            ocamldep=ocamldep,
            ocamlc=self.ocamlc,
            exe=ocamlopt,
            packages=packages,
            syntaxes=syntaxes,
            ppopts=ppopts,
            **kwargs)
