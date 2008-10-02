import os
import shutil
import types
import itertools
import re

# -----------------------------------------------------------------------------

def find_in_paths(filename, paths=None):
    if paths is None:
        paths = os.environ['PATH'].split(os.pathsep)

    for path in paths:
        f = os.path.join(path, filename)
        if os.path.exists(f):
            return Path(f)

    return None

def import_function(function):
    if isinstance(function, str):
        m, f = function.rsplit('.', 1)
        return getattr(__import__(m, {}, {}, ['']), f)
    return function

# -----------------------------------------------------------------------------

class Path(str):
    '''
    Implement a simple interface for working with the filesystem. This library
    is designed to be used as either Path('foo').glob(), or Path.glob('foo').

    By default, it's also possible to specify paths using '/' as the path
    separator, which will be replaced with the native separator during
    construction.
    '''

    def __new__(cls, *paths):
        s = ''

        for path in paths:
            if isinstance(path, str):
                s = os.path.join(s, path.replace('/', os.sep))
            else:
                s = os.path.join(s, *path)

        return str.__new__(cls, s)

    def __truediv__(self, rel):
        return Path(os.path.join(self, rel))

    def __rtruediv__(self, rel):
        return Path(os.path.join(rel, self))

    def __add__(self, rel):
        return Path(str.__add__(self, rel))

    def __repr__(self):
        return 'Path(%s)' % str.__repr__(self)

    # -------------------------------------------------------------------------
    # path manipulation functions

    split     = os.path.split
    split_ext = os.path.splitext

    def split_all(self):
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

    def relative_path(self):
        return Path.relative_path_to(self, os.getcwd())

    def relative_path_to(self, path):
        paths = Path.split_all(os.path.abspath(self))
        roots = Path.split_all(os.path.abspath(path))

        for i, (r, p) in enumerate(zip(roots, paths)):
            j = i
            if r != p:
                break
        else:
            i += 1
            j = len(roots)

        new_paths = [os.pardir] * (len(roots) - i) + paths[j:]

        if not new_paths:
            return Path(os.curdir)
        else:
            return Path(*new_paths)

    def replace_ext(self, ext):
        return Path(os.path.splitext(self)[0] + ext)

    def replace_suffixes(self, suffixes):
        try:
            ext = suffixes[self.ext]
        except KeyError:
            return self
        else:
            return self.replace_ext(ext)

    def replace_root(self, root):
        if not self.startswith(root):
            return Path(root, self)
        return self

    # -------------------------------------------------------------------------
    # state information

    @property
    def ext(self):
        return os.path.splitext(self)[1]

    @property
    def parent(self):
        return Path(os.path.dirname(self))

    @property
    def name(self):
        return Path(os.path.basename(self))

    @property
    def abspath(self):
        return Path(os.path.abspath(self))

    @property
    def normpath(self):
        return Path(os.path.normpath(self))

    ctime = property(os.path.getctime)
    mtime = property(os.path.getmtime)
    atime = property(os.path.getatime)

    exists  = os.path.exists
    isdir   = os.path.isdir
    isfile  = os.path.isfile
    islink  = os.path.islink
    ismount = os.path.ismount

    def md5(self):
        import hashlib
        with open(self, 'rb') as f:
            m = hashlib.md5()
            while True:
                d = f.read(8192)
                if not d:
                    break
                m.update(d)
            return m.digest()

    # -------------------------------------------------------------------------
    # path searching

    def find(self, name=None, include_dirs=True):
        for root, dirs, files in os.walk(self):
            if include_dirs:
                files = itertools.chain(files, dirs)

            for f in files:
                if name is not None and not Path.fnmatch(f, name):
                    continue

                yield Path(root, f)

    def fnmatch(self, pattern):
        import fbuild.fnmatch
        return fbuild.fnmatch.fnmatch(self, pattern)

    def glob(self, *, exclude=[]):
        import fbuild.fnmatch
        import fbuild.glob

        if isinstance(exclude, str):
            exclude = [exclude]

        for path in fbuild.glob.iglob(self):
            for pattern in exclude:
                if fbuild.fnmatch.fnmatch(path, pattern):
                    break
            else:
                yield Path(path)

    listdir = os.listdir

    # -------------------------------------------------------------------------
    # functions that modify the filesystem

    def make_dirs(self):
        '''
        Make the directories specified by this path. If they already exist
        and are already directories, don't raise an exception.
        '''

        try:
            os.makedirs(self)
        except OSError as e:
            if not (os.path.exists(self) and os.path.isdir(self)):
                raise e from e

    remove = os.remove

    def rmtree(self):
        shutil.rmtree(self)

    def copy(self, dst):
        shutil.copy(self, dst)

    def copy2(self, dst):
        shutil.copy2(self, dst)

    # -------------------------------------------------------------------------

    @classmethod
    def get_cwd(cls):
        return cls(os.getcwd())

    @classmethod
    def glob_all(cls, patterns):
        return [path for pattern in patterns for path in cls(pattern).glob()]

    @classmethod
    def replace_all_suffixes(cls, paths, suffixes):
        return [cls(path).replace_suffixes(suffixes) for path in paths]
