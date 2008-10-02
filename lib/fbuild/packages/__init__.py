import time

from fbuild import env, logger
from fbuild.path import Path
from fbuild.record import Record

# -----------------------------------------------------------------------------

class Package:
    default_config = None

    def __init__(self, *, config=None):
        self._is_dirty = None
        self._config = config

    def __getstate__(self):
        'Prepare data for serialization'

        # We can't cache the _is_dirty flag, or else we'd never recompute it.
        d = dict(self.__dict__)
        try:
            del d['_is_dirty']
        except KeyError:
            pass
        return d

    def __setstate__(self, state):
        'Load data from serializaton'
        self.__dict__.update(state)

        # We didn't cache the _is_dirty, so we need to manually set it
        self._is_dirty = None

    def state(self):
        return env.package_state(self)

    def is_dirty(self):
        if self._is_dirty is not None:
            return self._is_dirty

        try:
            timestamp = self.state().timestamp
        except AttributeError:
            self._is_dirty = True
            return True

        for dependency in self.dependencies():
            if self.is_dependency_dirty(dependency, timestamp):
                self._is_dirty = True
                return True

        self._is_dirty = False

        return False

    def is_dependency_dirty(self, dependency, timestamp):
        if isinstance(dependency, Package):
            return dependency.is_dirty()
        elif isinstance(dependency, Path):
            return not dependency.exists() or timestamp < dependency.getmtime()
        elif isinstance(dependency, str):
            path = Path(dependency)
            # assume it's a path
            return not path.exists() or timestamp < path.getmtime()
        else:
            raise ValueError('Bad argument: %r' % dependency)

    @property
    def config(self):
        if self._config is None and self.default_config:
            return env.cache(self.default_config)
        return self._config

    def build(self):
        state = self.state()

        if not self.is_dirty():
            return state.result

        result = self.run()
        self._is_dirty = False

        state.timestamp = time.time()
        state.result = result

        return result

    def run(self):
        raise NotImplementedError

# -----------------------------------------------------------------------------

class SimplePackage(Package):
    def __init__(self, target, *, config=None, **kwargs):
        super().__init__(config=config)

        self.target = target
        self.kwargs = kwargs

    def dependencies(self):
        return [self.target]

    def state(self):
        return super().state().setdefault(build(self.target), Record())

    def run(self):
        return self.command(build(self.target), **self.kwargs)

    def command(self):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.target)

class OneToOnePackage(Package):
    def __init__(self, dst, src, *, config=None, **kwargs):
        super().__init__(config=config)

        self.dst = dst
        self.src = src
        self.kwargs = kwargs

    def dependencies(self):
        return [self.src]

    def state(self):
        return super().state().setdefault(self.dst, Record())

    def run(self):
        return self.command(build(self.dst), build(self.src), **self.kwargs)

    def command(self):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.src)

class ManyToOnePackage(Package):
    def __init__(self, dst, srcs, *, config=None, **kwargs):
        super().__init__(config=config)

        self.dst = dst
        self.srcs = list(srcs)
        self.kwargs = kwargs

    def dependencies(self):
        return self.srcs

    def state(self):
        return super().state().setdefault(self.dst, Record())

    def run(self):
        return self.command(
            build(self.dst),
            build_srcs(self.srcs),
            **self.kwargs)

    def command(self):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.srcs)

# -----------------------------------------------------------------------------

class _CopyMove(OneToOnePackage):
    def state(self):
        src = Path(build(self.src))
        dst = Path(build(self.dst))
        if dst.isdir():
            dst = dst / src.name

        return super().state().setdefault(dst, Record())

    def run(self):
        src = Path(build(self.src))
        dst = Path(build(self.dst))

        dst.parent.make_dirs()
        if dst.isdir():
            dst = dst / src.name

        return self.command(dst, src)

class Copy(_CopyMove):
    def command(self, dst, src):
        logger.check(' * copy', '%s -> %s' % (src, dst),
            color='yellow')
        src.copy(dst)
        return dst

class Move(_CopyMove):
    def command(self, dst, src):
        logger.check(' * move', '%s -> %s' % (src, dst),
            color='yellow')
        src.move(dst)
        return dst

# -----------------------------------------------------------------------------

class BuilderWrapper(Package):
    def __init__(self, builder_class, packages, config=None, **kwargs):
        super().__init__(config=config)

        self.builder_class = builder_class
        self.packages = packages
        self.kwargs = kwargs

    def dependencies(self):
        return [p for p in self.packages if isinstance(p, (str, Package))]

    def run(self):
        packages = (build(package) for package in self.packages)
        return self.builder_class(*packages, **self.kwargs)

# -----------------------------------------------------------------------------

def build(src):
    if isinstance(src, Package):
        return src.build()
    return src

def build_srcs(srcs):
    results = []
    for src in srcs:
        result = build(src)
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
            paths.extend(Path(src).glob())
        else:
            # assume it's a list-like object
            paths.extend(Path.glob_all(src))

    return paths
