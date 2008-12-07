import collections
import hashlib
import itertools
import os
import shutil
import sys

import fbuild.fnmatch
import fbuild.glob

# ------------------------------------------------------------------------------

def find_in_paths(filename, paths=None):
    if paths is None:
        paths = os.environ['PATH'].split(os.pathsep)

    for path in paths:
        f = os.path.join(path, filename)
        if os.path.exists(f):
            return Path(f)

    return None

# ------------------------------------------------------------------------------

class Path(str):
    """Implement a simple interface for working with the filesystem. The
    methods in this class are designed to be used as either normal methods:

    >>> Path('foo/bar/baz.ext').split()
    (Path('foo/bar'), Path('baz.ext'))

    or static methods:

    >>> Path.split('foo/bar/baz.ext')
    (Path('foo/bar'), Path('baz.ext'))

    By default, it's also possible to specify paths using '/' as the path
    separator, which will be replaced with the native separator during
    construction.
    """

    def __new__(cls, *paths):
        s = ''
        for path in paths:
            if isinstance(path, str):
                s = os.path.join(s, path.replace('/', os.sep))
            else:
                s = os.path.join(s, *path)

        return str.__new__(cls, s)

    def __truediv__(self, rel):
        """Joins this path with a string

        >>> Path('foo/bar/baz') / 'boo'
        Path('foo/bar/baz/boo')
        """
        return Path(self, rel)

    def __rtruediv__(self, rel):
        """Joins the path with a string
        >>> 'boo' / Path('foo/bar/baz')
        Path('boo/foo/bar/baz')
        """
        return Path(rel, self)

    def __add__(self, rel):
        """Add a path and a string together and return a new Path object.

        >>> Path('foo/bar/baz') + '.ext'
        Path('foo/bar/baz.ext')
        >>> Path('foo/bar/baz') + Path('boo')
        Path('foo/bar/bazboo')
        """
        return Path(str.__add__(self, rel))

    def __repr__(self):
        return 'Path(%s)' % str.__repr__(self.replace(os.sep, '/'))

    # -------------------------------------------------------------------------
    # properties

    @property
    def ext(self):
        """Return the path's extension.

        >>> Path('foo/bar/baz.ext').ext
        '.ext'
        """
        return os.path.splitext(self)[1]

    @property
    def name(self):
        """Return the path's relative name.

        >>> Path('foo/bar/baz.ext').name
        Path('baz.ext')
        """
        return Path(os.path.basename(self))

    @property
    def parent(self):
        """Return the path's parent directory.

        >>> Path('foo/bar/baz.ext').parent
        Path('foo/bar')
        """
        return Path(os.path.dirname(self))

    # -------------------------------------------------------------------------
    # methods

    access = os.access

    def addprefix(self, prefix):
        """Add the prefix before the basename of the path.

        >>> Path.addprefix('foo/bar/baz.ext', 'boo')
        Path('foo/bar/boobaz.ext')
        """
        dirname, basename = os.path.split(self)
        return Path(dirname, prefix + basename)

    def addroot(self, root):
        """Add the root of the path with "root", unless it already starts with
        "root". It uses character subsitution, so it could generate invalid
        paths.

        >>> Path.addroot('foo/bar/baz.ext', 'abc')
        Path('abc/foo/bar/baz.ext')
        >>> Path.addroot('foo/bar/baz.ext', 'foo')
        Path('foo/bar/baz.ext')
        """
        if not self.startswith(root):
            return Path(root, self)
        return Path(self)

    def abspath(self):
        """Return the absolute version of a path."""
        return os.path.abspath(self)

    def basename(self):
        """Returns the final component of a pathname

        >>> Path.basename('foo/bar/baz.ext')
        Path('baz.ext')
        """
        return Path(os.path.basename(self))

    chmod = os.chmod
    commonprefix = os.path.commonprefix
    copy = shutil.copy
    copy2 = shutil.copy2
    copyfile = shutil.copyfile
    copymode = shutil.copymode
    copystat = shutil.copystat
    copytree = shutil.copytree

    def dirname(self):
        """Returns the directory component of a pathname.

        >>> Path.dirname('foo/bar/baz.ext')
        Path('foo/bar')
        """
        return Path(os.path.dirname(self))

    exists = os.path.exists

    def expanduser(self):
        """Expand ~ and ~user constructs.  If user or $HOME is unknown, do
        nothing."""
        return Path(os.path.expanduser(self))

    def expandvars(self):
        """Expand shell variables of form $var and ${var}.  Unknown variables
        are left unchanged."""
        return Path(os.path.expandvars(self))

    def find(self, pattern=None, *, include_dirs=True):
        """Search the filesystem starting from this path. If "pattern" is
        specified, return files matching the pattern."""
        for root, dirs, files in os.walk(self):
            if include_dirs:
                files = itertools.chain(files, dirs)

            for f in files:
                if name is not None and not Path.fnmatch(f, pattern):
                    continue

                yield Path(root, f)

    def fnmatch(self, pattern):
        """Returns True if the path matches the pattern.

        >>> Path.fnmatch('foo.ext', 'foo?ext')
        True
        >>> Path.fnmatch('foo.ext', 'foo*')
        True
        >>> Path.fnmatch('foo.ext', 'foo.{ext,bar}')
        True
        >>> Path.fnmatch('foo.bar', 'foo.{ext,bar}')
        True
        >>> Path.fnmatch('bar.ext', 'foo?ext')
        False
        >>> Path.fnmatch('bar.ext', 'foo*')
        False
        >>> Path.fnmatch('foo.baz', 'foo.{ext,bar}')
        False
        """
        return fbuild.fnmatch.fnmatch(self, pattern)

    getatime = os.path.getatime
    getctime = os.path.getctime
    getmtime = os.path.getmtime
    getsize = os.path.getsize

    def glob(self, *, exclude=[]):
        """Iterprets the path as a glob and yields all the matching files."""
        if isinstance(exclude, str):
            exclude = [exclude]

        for path in fbuild.glob.iglob(self):
            for pattern in exclude:
                if fbuild.fnmatch.fnmatch(path, pattern):
                    break
            else:
                yield Path(path)

    isabs = os.path.isabs
    isdir = os.path.isdir

    def isdirty(self, *dependencies):
        """Returns True if the path doesn't exist or the modification time
        predates any of the dependencies."""
        if not os.path.exists(self):
            return True

        timestamp = os.path.getmtime(self)

        for dep in dependencies:
            for d in (dep,) if isinstance(dep, str) else dep:
                if isinstance(d, Path) and timestamp < os.path.getmtime(d):
                    return True

        return False

    isfile = os.path.isfile
    islink = os.path.islink
    ismount = os.path.ismount
    lexists = os.path.lexists

    def listdir(self):
        """Returns all the files in the path."""
        return [Path(f) for f in os.listdir(f)]

    lstat = os.lstat

    def makedirs(self, *args, **kwargs):
        """Make the directories specified by this path. If they already exist
        and are already directories, don't raise an exception.
        """
        # We want an error thrown if the file exists and is not a directory.
        if os.path.exists(self) and os.path.isdir(self):
            return
        os.makedirs(self, *args, **kwargs)

    def md5(self, chunksize=65536):
        """Hash the file usind md5 and return the digest."""
        with open(self, 'rb') as f:
            m = hashlib.md5()
            while True:
                d = f.read(chunksize)
                if not d:
                    break
                m.update(d)
            return m.hexdigest()

    mkdir = os.mkdir
    mknod = os.mknod
    move = shutil.move

    def normcase(self):
        """Normalize case of pathname.  Has no effect under Posix."""
        return Path(os.path.normcase(self))

    def normpath(self):
        """Normalize path, eliminating double slashes, etc."""
        return Path(os.path.normpath(self))

    def realpath(self):
        """Return the canonical path of the specified filename, eliminating any
        symbolic links encountered in the path."""
        return Path(os.path.realpath(self))


    def relpath(self, start=None):
        """Return a relative version of a path.

        >>> Path.relpath('foo/bar/baz.ext', 'foo/baz')
        Path('../bar/baz.ext')
        """
        return Path(os.path.relpath(self, start))

    remove = os.remove
    removedirs = os.removedirs
    rename = os.rename
    renames = os.renames
    rmdir = os.rmdir
    rmtree = shutil.rmtree

    def split(self):
        """Split a pathname.  Returns tuple "(head, tail)" where "tail" is
        everything after the final slash.  Either part may be empty.

        >>> Path.split('foo/bar/baz.ext')
        (Path('foo/bar'), Path('baz.ext'))
        """
        dirname, basename = os.path.split(self)
        return Path(dirname), Path(basename)

    def splitall(self):
        """Split a pathname into all of it's components.

        >>> Path.splitall('foo/bar/baz.ext')
        [Path('foo'), Path('bar'), Path('baz.ext')]
        """
        paths = []
        old_path = path = self

        while True:
            path, filename = os.path.split(path)

            if path == old_path:
                if path:
                    paths.append(path)
                break
            else:
                old_path = path
                paths.append(Path(filename))
        paths.reverse()
        return paths

    def splitdrive(self):
        """Split a pathname into drive and path. On Posix, drive is always
        empty."""
        drive, tail = os.path.splitdrive(self)
        return Path(drive), tail

    def splitext(self):
        """Split the extension from a pathname.

        Extension is everything from the last dot to the end, ignoring
        leading dots.  Returns "(root, ext)"; ext may be empty.

        >>> Path.splitext('foo/bar/baz.ext')
        (Path('foo/bar/baz'), '.ext')
        """
        root, ext = os.path.splitext(self)
        return Path(root), ext

    stat = os.stat

    def replaceext(self, ext):
        """Replace the extension with "ext".

        >>> Path.replaceext('foo/bar/baz.ext', '.boo')
        Path('foo/bar/baz.boo')
        """
        return Path(os.path.splitext(self)[0] + ext)

    def replaceexts(self, extensions):
        """If the path's extension ends with any of the keys in "extensions",
        replace it with that value.

        >>> Path.replaceexts('foo/bar/baz.ext', {'.abc':'.foo', '.ext': '.bar'})
        Path('foo/bar/baz.bar')
        >>> Path.replaceexts('foo/bar/baz.boo', {'.abc':'.foo', '.ext': '.bar'})
        Path('foo/bar/baz.boo')
        """
        root, ext = os.path.splitext(self)
        try:
            ext = extensions[ext]
        except KeyError:
            return Path(self)
        else:
            return Path(root + ext)

    utime = os.utime

    def walk(self, *args, **kwargs):
        """Walk the filesystem just like os.walk. Returns "(dirpath, dirnames,
        filenames)". "dirpath" is automatically converted into a path, but
        "dirnames" and "filenames" is not since that can be modified by the
        user to limit which directories to walk down."""
        for dirpath, dirnames, filenames in os.walk(self, *args, **kwargs):
            yield Path(dirpath), dirnames, filenames

    # --------------------------------------------------------------------------
    # os-specific functions

    if 'posix' in sys.builtin_module_names:
        chflags = os.chflags
        chroot = os.chroot
        chown = os.chown
        lchflags = os.lchflags
        lchmod = os.lchmod
        lchown = os.lchown
        link = os.link
        mkfifo = os.mkfifo
        readlink = os.readlink
        statvfs = os.statvfs
        samefile = os.path.samefile
        symlink = os.symlink

    elif 'nt' in sys.builtin_module_names:
        def splitunc(self):
            """Split a pathname into UNC mount point and relative path
            specifiers.

            Return a 2-tuple (unc, rest); either part may be empty.  If unc is
            not empty, it has the form '//host/mount' (or similar using
            backslashes).  unc+rest is always the input path.  Paths containing
            drive letters never have an UNC part."""
            unc, rest = os.path.splitunc(self)
            return Path(unc), Path(rest)

    # -------------------------------------------------------------------------
    # static methods

    @staticmethod
    def getcwd():
        """Return the current directory."""
        return Path(os.getcwd())

    @staticmethod
    def globall(patterns, *args, **kwargs):
        """"Glob each of the "patterns" and yields the results. If an item in
        "patterns" is not a string, it is assumed to be iterable and each
        subitem is globbed and added to the list."""
        for pattern in patterns:
            if \
                    not isinstance(pattern, str) and \
                    isinstance(pattern, collections.Iterable):
                paths = Path.globall(pattern)
            else:
                paths = Path.glob(pattern, *args, **kwargs)

            for path in paths:
                yield path
