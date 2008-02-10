import os
import fnmatch
import glob
import types

# -----------------------------------------------------------------------------

def splitall(path):
    paths = []
    old_path = path

    while True:
        path, filename = os.path.split(path)

        if path == old_path:
            if path:
                paths.append(path)
            break
        else:
            old_path = path
            paths.append(filename)
    paths.reverse()
    return paths


def relativepath(root, path):
    roots = splitall(os.path.abspath(root))
    paths = splitall(os.path.abspath(path))

    for i, (r, p) in enumerate(zip(roots, paths)):
        j = i
        if r != p:
            break
    else:
        i += 1
        j = len(roots)

    new_paths = ['..'] * (len(roots) - i) + paths[j:]

    if not new_paths:
        return '.'
    else:
        return os.path.join(*new_paths)


def find(path, name=None, include_dirs=True):
    for root, dirs, files in os.walk(path):
        if include_dirs:
            files += dirs

        for f in files:
            if name is not None and not fnmatch.fnmatch(f, name):
                continue

            yield os.path.join(root, f)


def find_in_paths(filename, paths=None):
    if paths is None:
        paths = os.environ['PATH'].split(os.pathsep)

    for path in paths:
        f = os.path.join(path, filename)
        if os.path.exists(f):
            return f

    return None


def make_path(path, prefix=None, suffix=None, root=None):
    # if the path is not a string, assume it's a list of path elements
    if not isinstance(path, str):
        path = os.path.join(*path)

    if root is not None:
        path = os.path.join(root, path)

    if prefix is not None:
        dirname, basename = os.path.split(path)
        path = os.path.join(dirname, prefix + basename)

    if suffix is not None:
        path += suffix

    return path


def glob_paths(paths, root=None):
    new_paths = []
    for path in paths:
        new_paths.extend(glob.glob(make_path(path, root=root)))
    return new_paths


def import_function(function):
    if isinstance(function, str):
        m, f = function.rsplit('.', 1)
        return getattr(__import__(m, {}, {}, ['']), f)
    return function

def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
