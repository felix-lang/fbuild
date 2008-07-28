import time

import fbuild

# -----------------------------------------------------------------------------

class Package:
    def __init__(self):
        self._is_dirty = None

    def data(self, conf):
        return conf.setdefault(
            'packages', {}).setdefault(
                '%s:%s' % (self.__module__, self.__class__.__name__), {})

    def is_dirty(self, conf):
        if self._is_dirty is not None:
            return self._is_dirty

        try:
            timestamp = self.data(conf)['timestamp']
        except KeyError:
            self._is_dirty = True
            return True

        for dependency in self.dependencies(conf):
            if self.is_dependency_dirty(conf, dependency, timestamp):
                self._is_dirty = True
                return True

        self._is_dirty = False

        return False

    def is_dependency_dirty(self, conf, dependency, timestamp):
        if isinstance(dependency, Package):
            return dependency.is_dirty(conf)
        elif isinstance(dependency, fbuild.Path):
            return timestamp < dependency.mtime
        elif isinstance(dependency, str):
            # assume it's a path
            return timestamp < fbuild.Path(dependency).mtime
        else:
            raise ValueError('Bad argument: %r' % dependency)

    def build(self, conf):
        data = self.data(conf)

        if not self.is_dirty(conf):
            return data['result']

        result = self.run(conf)
        self._is_dirty = False

        data['timestamp'] = time.time()
        data['result'] = result

        return result

    def run(self, conf):
        raise NotImplementedError

# -----------------------------------------------------------------------------

class SimplePackage(Package):
    def __init__(self, target, **kwargs):
        super().__init__()

        self.target = target
        self.kwargs = kwargs

    def dependencies(self, conf):
        return [self.target]

    def data(self, conf):
        return super().data(conf).setdefault(self.target, {})

    def run(self, conf):
        return self.command(conf, build(conf, self.target), **self.kwargs)

    def command(self, conf):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.target)

class OneToOnePackage(Package):
    def __init__(self, dst, src, **kwargs):
        super().__init__()

        self.dst = dst
        self.src = src
        self.kwargs = kwargs

    def dependencies(self, conf):
        return [self.src]

    def data(self, conf):
        return super().data(conf).setdefault(self.dst, {})

    def run(self, conf):
        return self.command(conf,
            build(conf, self.dst),
            build(conf, self.src),
            **self.kwargs)

    def command(self, conf):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.src)

class ManyToOnePackage(Package):
    def __init__(self, dst, srcs, **kwargs):
        super().__init__()

        self.dst = dst
        self.srcs = srcs
        self.kwargs = kwargs

    def dependencies(self, conf):
        return self.srcs

    def data(self, conf):
        return super().data(conf).setdefault(self.dst, {})

    def run(self, conf):
        return self.command(conf,
            build(conf, self.dst),
            build_srcs(conf, self.srcs),
            **self.kwargs)

    def command(self, conf):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.srcs)

# -----------------------------------------------------------------------------

class Copy(OneToOnePackage):
    def command(self, conf, dst, src):
        fbuild.logger.check(' * copy', '%s -> %s' % (src, dst), color='yellow')
        src.copy(dst)
        return dst

class Move(OneToOnePackage):
    def command(self, conf, dst, src):
        fbuild.logger.check(' * move', '%s -> %s' % (src, dst), color='yellow')
        src.move(dst)
        return dst

# -----------------------------------------------------------------------------

def build(conf, src):
    if isinstance(src, Package):
        return src.build(conf)
    return src

def build_srcs(conf, srcs):
    results = []
    for src in srcs:
        result = build(conf, src)
        if isinstance(result, str):
            results.append(result)
        else:
            # assume it's iterable
            results.extend(result)
    return results

def glob_paths(srcs):
    paths = []
    for src in srcs:
        if isinstance(src, Package):
            paths.append(src)
        elif isinstance(src, str):
            paths.extend(fbuild.Path(src).glob())
        else:
            # assume it's a list-like object
            paths.extend(fbuild.Path.glob_all(src))

    return paths
