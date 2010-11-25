import abc
import functools
import hashlib
import itertools
import pprint
import threading
import types

import fbuild
import fbuild.functools
import fbuild.inspect
import fbuild.path
import fbuild.rpc

import fbuild.db.pickle_backend

# ------------------------------------------------------------------------------

class SRC:
    """An annotation that's used to designate an argument as a source path."""
    @staticmethod
    def convert(src):
        return [src]

class SRCS(SRC):
    """An annotation that's used to designate an argument as a list of source
    paths."""
    @staticmethod
    def convert(srcs):
        return srcs

class DST:
    """An annotation that's used to designate an argument is a destination
    path."""
    @staticmethod
    def convert(dst):
        return [dst]

class DSTS(DST):
    """An annotation that's used to designate an argument is a list of
    destination paths."""
    @staticmethod
    def convert(dsts):
        return dsts

class OPTIONAL_SRC(SRC):
    """An annotation that's used to designate an argument as a source path or
    None."""
    @staticmethod
    def convert(src):
        if src is None:
            return []
        return [src]

class OPTIONAL_DST(DST):
    """An annotation that's used to designate an argument as a destination path
    or None."""
    @staticmethod
    def convert(dst):
        if dst is None:
            return []
        return [dst]

# ------------------------------------------------------------------------------

class Database:
    """L{Database} persistently stores the results of argument calls."""

    def __init__(self, ctx, explain=False):
        def handle_rpc(msg):
            method, args, kwargs = msg
            return method(*args, **kwargs)

        self._ctx = ctx
        self._explain = explain
        self._backend = fbuild.db.pickle_backend.PickleBackend(ctx)
        self._rpc = fbuild.rpc.RPC(handle_rpc)
        self._rpc.daemon = True
        self.start()

    def start(self):
        """Start the server thread."""
        self._rpc.start()

    def shutdown(self, *args, **kwargs):
        """Inform and wait for the L{DatabaseThread} to shut down."""
        self._rpc.join(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Save the database to the file."""
        return self._rpc.call((self._backend.save, args, kwargs))

    def load(self, *args, **kwargs):
        """Load the database from the file."""
        return self._rpc.call((self._backend.load, args, kwargs))

    def call(self, function, *args, **kwargs):
        """Call the function and return the result, src dependencies, and dst
        dependencies. If the function has been previously called with the same
        arguments, return the cached results.  If we detect that the function
        changed, throw away all the cached values for that function. Similarly,
        throw away all of the cached values if any of the optionally specified
        "srcs" are also modified.  Finally, if any of the filenames in "dsts"
        do not exist, re-run the function no matter what."""

        # Make sure none of the arguments are a generator.
        assert all(not fbuild.inspect.isgenerator(arg)
            for arg in itertools.chain(args, kwargs.values())), \
            "Cannot store generator in database"

        function_name, function, args, kwargs = self._find_function_name(
            function,
            args,
            kwargs)

        # Compute the function digest.
        function_digest = self._digest_function(function, args, kwargs)

        # Find the call filenames for the function.
        bound, srcs, dsts, return_type = self._find_call_filenames(
            function,
            args,
            kwargs)

        function_dirty, call_id, old_result, call_file_digests, \
            external_dirty, external_srcs, external_dsts, external_digests = \
                self._rpc.call((
                    self._backend.prepare,
                    (function_name, function_digest, bound, srcs, dsts),
                    {}))

        dirty_dsts = set()

        # Check if we have a result. If not, then we're dirty.
        if not (function_dirty or \
                call_id is None or \
                call_file_digests or \
                external_digests or \
                external_dirty):
            # If the result is a dst filename, make sure it exists. If not,
            # we're dirty.
            if return_type is not None and issubclass(return_type, DST):
                return_dsts = return_type.convert(old_result)
            else:
                return_dsts = ()

            for dst in itertools.chain(
                    return_dsts,
                    dsts,
                    external_dsts):
                if not fbuild.path.Path(dst).exists():
                    dirty_dsts.add(dst)
                    break
            else:
                # The call was not dirty, so return the cached value.
                all_srcs = srcs.union(external_srcs)
                all_dsts = dsts.union(external_dsts)
                all_dsts.update(return_dsts)
                return old_result, all_srcs, all_dsts

        if self._explain:
            # Explain why we are going to run the function.
            if function_dirty:
                self._ctx.logger.log('function %s is dirty' % function_name)

            if call_id is None:
                self._ctx.logger.log(
                    'function %s has not been called with these arguments' %
                    function_name)

            if call_file_digests:
                self._ctx.logger.log('dirty source files:')
                for src, digest in call_file_digests:
                    self._ctx.logger.log('\t%s %s' % (digest, src))

            if external_digests:
                self._ctx.logger.log('dirty external digests:')
                for src, digest in external_digests:
                    self._ctx.logger.log('\t%s %s' % (digest, src))

            if dirty_dsts:
                self._ctx.logger.log('destination files do not exist:')
                for dst in dirty_dsts:
                    self._ctx.logger.log('\t%s' % dst)

        # Clear external srcs and dsts since they'll be recomputed inside
        # the function.
        external_srcs = set()
        external_dsts = set()

        # The call was dirty, so recompute it.
        result = function(*args, **kwargs)

        # Make sure the result is not a generator.
        assert not fbuild.inspect.isgenerator(result), \
            "Cannot store generator in database"

        # Save the results in the database.
        self._rpc.call((
            self._backend.cache,
            (function_dirty, function_name, function_digest,
                call_id, bound, result, call_file_digests, external_srcs,
                external_dsts, external_digests),
            {}))

        if return_type is not None and issubclass(return_type, DST):
            return_dsts = return_type.convert(result)
        else:
            return_dsts = ()

        all_srcs = srcs.union(external_srcs)
        all_dsts = dsts.union(external_dsts)
        all_dsts.update(return_dsts)
        return result, all_srcs, all_dsts

    def clear_function(self, *args, **kwargs):
        """Clear the function from the database."""

        return self._rpc.call((
            self._backend.clear_function,
            args,
            kwargs))

    def clear_file(self, *args, **kwargs):
        """Clear the file from the database."""

        return self._rpc.call((
            self._backend.clear_file,
            args,
            kwargs))

    def dump_database(self):
        """Print the database."""
        pprint.pprint(self._backend.__dict__)

    def _find_function_name(self, function, args, kwargs):
        """Extract the function name from the function."""

        if not fbuild.inspect.ismethod(function):
            function_name = function.__module__ + '.' + function.__name__
        else:
            # If we're caching a PersistentObject creation, use the class's
            # name as our function name.
            if function.__name__ == '__call_super__' and \
                    isinstance(function.__self__, PersistentMeta):
                function_name = '%s.%s' % (
                    function.__self__.__module__,
                    function.__self__.__name__)
            else:
                function_name = '%s.%s.%s' % (
                    function.__module__,
                    function.__self__.__class__.__name__,
                    function.__name__)
            args = (function.__self__,) + args
            function = function.__func__

        if not fbuild.inspect.isroutine(function):
            function = function.__call__

        return function_name, function, args, kwargs

    # Create an in-process cache of the function digests, since they shouldn't
    # change while we're running.
    _digest_function_lock = threading.Lock()
    _digest_function_cache = {}
    def _digest_function(self, function, args, kwargs):
        """Compute the digest for a function or a function object. Cache this
        for this instance."""
        with self._digest_function_lock:
            # If we're caching a PersistentObject creation, use the class's
            # __init__ as our function.
            if fbuild.inspect.isroutine(function) and \
                    len(args) > 0 and \
                    function.__name__ == '__call_super__' and \
                    isinstance(args[0], PersistentMeta):
                function = args[0].__init__

            try:
                digest = self._digest_function_cache[function]
            except KeyError:
                if fbuild.inspect.isroutine(function):
                    # The function is a function, method, or lambda, so digest
                    # the source. If the function is a builtin, we will raise
                    # an exception.
                    src = fbuild.inspect.getsource(function)
                    digest = hashlib.md5(src.encode()).hexdigest()
                else:
                    # The function is a functor so let it digest itself.
                    digest = hash(function)
                self._digest_function_cache[function] = digest

        return digest

    def _find_call_filenames(self, function, args, kwargs):
        """Return the filenames needed for the function."""

        # Bind the arguments so that we can look up normal args by name.
        bound = fbuild.functools.bind_args(function, args, kwargs)

        # Check if any of the files changed.
        return_type = None
        srcs = set()
        dsts = set()
        for akey, avalue in function.__annotations__.items():
            if akey == 'return':
                return_type = avalue
            elif issubclass(avalue, SRC):
                srcs.update(avalue.convert(bound[akey]))
            elif issubclass(avalue, DST):
                dsts.update(avalue.convert(bound[akey]))

        return bound, srcs, dsts, return_type

    def add_external_dependencies_to_call(self, *, srcs=(), dsts=()):
        """When inside a cached method, register additional src
        dependencies for the call. This function can only be called from
        a cached function and will error out if it is called from an
        uncached function."""

        # Hack in additional dependencies
        i = 2
        try:
            while True:
                frame = fbuild.inspect.currentframe(i)
                try:
                    if frame.f_code == self.call.__code__:
                        function_name = frame.f_locals['function_name']
                        call_id = frame.f_locals['call_id']
                        external_digests = frame.f_locals['external_digests']
                        external_srcs = frame.f_locals['external_srcs']
                        external_dsts = frame.f_locals['external_dsts']

                        for src in srcs:
                            external_srcs.add(src)
                            dirty, digest = self._rpc.call((
                                self._backend.check_call_file,
                                (call_id, function_name, src),
                                {}))
                            if dirty:
                                external_digests.append((src, digest))

                        external_dsts.update(dsts)
                    i += 1
                finally:
                    del frame
        except ValueError:
            pass

# ------------------------------------------------------------------------------


class PersistentMeta(abc.ABCMeta):
    """A metaclass that searches the db for an already instantiated class with
    the same arguments.  It subclasses from ABCMeta so that subclasses can
    implement abstract methods."""
    def __call_super__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

    def __call__(cls, ctx, *args, **kwargs):
        result, srcs, objs = ctx.db.call(cls.__call_super__, ctx,
            *args, **kwargs)

        return result

class PersistentObject(metaclass=PersistentMeta):
    """An abstract baseclass that will cache instances in the database."""

    def __init__(self, ctx):
        self.ctx = ctx

# ------------------------------------------------------------------------------

class caches:
    """L{caches} decorates a function and caches the results.  The first
    argument of the function must be an instance of L{database}.

    >>> ctx = fbuild.context.make_default_context()
    >>> @caches
    ... def test(ctx):
    ...     print('running test')
    ...     return 5
    >>> test(ctx)
    running test
    5
    >>> test(ctx)
    5
    """

    def __init__(self, function):
        functools.update_wrapper(self, function)
        self.function = function

    def __call__(self, *args, **kwargs):
        result, srcs, dsts = self.call(*args, **kwargs)
        return result

    def call(self, ctx, *args, **kwargs):
        return ctx.db.call(self.function, ctx, *args, **kwargs)

class cachemethod:
    """L{cachemethod} decorates a method of a class to cache the results.

    >>> ctx = fbuild.context.make_default_context([])
    >>> class C:
    ...     def __init__(self, ctx):
    ...         self.ctx = ctx
    ...     @cachemethod
    ...     def test(self):
    ...         print('running test')
    ...         return 5
    >>> c = C(ctx)
    >>> c.test()
    running test
    5
    >>> c.test()
    5
    """
    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return cachemethod_wrapper(types.MethodType(self.method, instance))

class cachemethod_wrapper:
    def __init__(self, method):
        self.method = method

    def __call__(self, *args, **kwargs):
        result, srcs, dsts = self.call(*args, **kwargs)
        return result

    def call(self, *args, **kwargs):
        return self.method.__self__.ctx.db.call(self.method, *args, **kwargs)

class cacheproperty:
    """L{cacheproperty} acts like a normal I{property} but will memoize the
    result in the store.  The first argument of the function it wraps must be a
    store or a class that has has an attribute named I{store}.

    >>> ctx = fbuild.context.make_default_context([])
    >>> class C:
    ...     def __init__(self, ctx):
    ...         self.ctx = ctx
    ...     @cacheproperty
    ...     def test(self):
    ...         print('running test')
    ...         return 5
    >>> c = C(ctx)
    >>> c.test
    running test
    5
    >>> c.test
    5
    """
    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        if instance is None:
            return self
        result, srcs, dsts = self.call(instance)
        return result

    def call(self, instance):
        return instance.ctx.db.call(types.MethodType(self.method, instance))
