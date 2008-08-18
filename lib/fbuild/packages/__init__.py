import time

from fbuild import logger, Path, Record

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

    def state(self, env):
        return env.package_state(self)

    def is_dirty(self, env):
        if self._is_dirty is not None:
            return self._is_dirty

        try:
            timestamp = self.state(env).timestamp
        except AttributeError:
            self._is_dirty = True
            return True

        for dependency in self.dependencies(env):
            if self.is_dependency_dirty(env, dependency, timestamp):
                self._is_dirty = True
                return True

        self._is_dirty = False

        return False

    def is_dependency_dirty(self, env, dependency, timestamp):
        if isinstance(dependency, Package):
            return dependency.is_dirty(env)
        elif isinstance(dependency, Path):
            return timestamp < dependency.mtime
        elif isinstance(dependency, str):
            # assume it's a path
            return timestamp < Path(dependency).mtime
        else:
            raise ValueError('Bad argument: %r' % dependency)

    def config(self, env):
        if self._config is None and self.default_config:
            return env.config(self.default_config)
        return self._config

    def build(self, env):
        state = self.state(env)

        if not self.is_dirty(env):
            return state.result

        result = self.run(env)
        self._is_dirty = False

        state.timestamp = time.time()
        state.result = result

        return result

    def run(self, env):
        raise NotImplementedError

# -----------------------------------------------------------------------------

class SimplePackage(Package):
    def __init__(self, target, *, config=None, **kwargs):
        super().__init__(config=config)

        self.target = target
        self.kwargs = kwargs

    def dependencies(self, env):
        return [self.target]

    def state(self, env):
        return super().state(env).setdefault(self.target, Record())

    def run(self, env):
        return self.command(env, build(env, self.target), **self.kwargs)

    def command(self, env):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.target)

class OneToOnePackage(Package):
    def __init__(self, dst, src, *, config=None, **kwargs):
        super().__init__(config=config)

        self.dst = dst
        self.src = src
        self.kwargs = kwargs

    def dependencies(self, env):
        return [self.src]

    def state(self, env):
        return super().state(env).setdefault(self.dst, Record())

    def run(self, env):
        return self.command(env,
            build(env, self.dst),
            build(env, self.src),
            **self.kwargs)

    def command(self, env):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.src)

class ManyToOnePackage(Package):
    def __init__(self, dst, srcs, *, config=None, **kwargs):
        super().__init__(config=config)

        self.dst = dst
        self.srcs = srcs
        self.kwargs = kwargs

    def dependencies(self, env):
        return self.srcs

    def state(self, env):
        return super().state(env).setdefault(self.dst, Record())

    def run(self, env):
        return self.command(env,
            build(env, self.dst),
            build_srcs(env, self.srcs),
            **self.kwargs)

    def command(self, env):
        raise NotImplementedError

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.dst, self.srcs)

# -----------------------------------------------------------------------------

class Copy(OneToOnePackage):
    def command(self, env, dst, src):
        logger.check(' * copy', '%s -> %s' % (src, dst), color='yellow')
        src.copy(dst)
        return dst

class Move(OneToOnePackage):
    def command(self, env, dst, src):
        logger.check(' * move', '%s -> %s' % (src, dst), color='yellow')
        src.move(dst)
        return dst

# -----------------------------------------------------------------------------

def build(env, src):
    if isinstance(src, Package):
        return src.build(env)
    return src

def build_srcs(env, srcs):
    results = []
    for src in srcs:
        result = build(env, src)
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
