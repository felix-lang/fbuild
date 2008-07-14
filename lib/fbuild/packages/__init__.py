import os
import time

import fbuild
import fbuild.path

# -----------------------------------------------------------------------------

class AbstractPackage:
    def __init__(self, target=None):
        self.target = target
        self._is_dirty = None

    def is_dirty(self, conf):
        return True

    def data(self, conf):
        data = conf.setdefault(
            'packages', {}).setdefault(
                '%s:%s' % (self.__module__, self.__class__.__name__), {})
        data.setdefault(self.target, {})
        return data

    def build(self, conf):
        data = self.data(conf)

        if not self.is_dirty(conf):
            return data[self.target]['result']

        result = self.run(conf)
        self._is_dirty = False

        data[self.target]['timestamp'] = time.time()
        data[self.target]['result'] = result

        return result

    def run(self, conf):
        raise NotImplementedError

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self.target)

# -----------------------------------------------------------------------------

class FilePackage(AbstractPackage):
    def __init__(self, target):
        super().__init__(fbuild.path.make_path(target))

    def dependencies(self, conf):
        return []

    def is_dirty(self, conf):
        if self._is_dirty is not None:
            return self._is_dirty

        try:
            timestamp = self.data(conf)[self.target]['timestamp']
        except KeyError:
            self._is_dirty = True
            return True

        for src in self.dependencies(conf):
            if isinstance(src, AbstractPackage):
                if src.is_dirty(conf):
                    self._is_dirty = True
                    return True
            else:
                if timestamp < os.path.getmtime(src):
                    self._is_dirty = True
                    return True

        self._is_dirty = False
        return False

# -----------------------------------------------------------------------------

class SimplePackage(FilePackage):
    def __init__(self, target, **kwargs):
        super().__init__(target)
        self.kwargs = kwargs

    def run(self, conf, *args, **kwargs):
        return self.command(conf)(build(conf, self.target),
            *args, **dict(self.kwargs, **kwargs))

    def command(self, conf):
        raise NotImplementedError

# -----------------------------------------------------------------------------

def build(conf, src):
    if isinstance(src, AbstractPackage):
        return src.build(conf)
    return src

def build_srcs(conf, srcs):
    new_srcs = []
    for src in srcs:
        src = build(conf, src)
        if isinstance(src, str):
            new_srcs.append(src)
        else:
            # assume it's iterable
            new_srcs.extend(src)
    return new_srcs

def glob_paths(srcs):
    new_srcs = []
    for src in srcs:
        if isinstance(src, AbstractPackage):
            new_srcs.append(src)
        else:
            try:
                paths = fbuild.path.glob_paths([src])
            except TypeError:
                new_srcs.append(src)
            else:
                new_srcs.extend(paths)
    return new_srcs
