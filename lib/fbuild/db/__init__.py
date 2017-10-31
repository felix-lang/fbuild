import abc
import functools
import types
import itertools
import inspect
import fbuild

# ------------------------------------------------------------------------------


_CTX_ERRORS = {
    'caches.call': "'%s' expects a Context object as its first argument, but " \
                   "it was given a '%s' object instead.",
    'PersistentMeta.__call__': "'%s.__init__' expects a Context object as " \
                               "its first argument, but it was given a '%s' " \
                               "object instead.",
    'cache<member>.call': "'%s.ctx' is supposed to be a Context " \
                          "object, but it has been modified to instead " \
                          "be a '%s' object.",
}


def _check_ctx(ctx, name, kind):
    """Ensure that the given object is a Context object."""

    from fbuild.context import Context

    if not isinstance(ctx, Context):
        raise TypeError(_CTX_ERRORS[kind] % (name, type(ctx).__name__))


def _update_fun_map(fun):
    """Add the given function to the global function map."""

    # Prevent a circular import.
    from .database import Database
    Database.add_function_to_map(fun)

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


class PersistentMeta(abc.ABCMeta):
    """A metaclass that searches the db for an already instantiated class with
    the same arguments.  It subclasses from ABCMeta so that subclasses can
    implement abstract methods."""
    def __init__(cls, name, bases, dict_):
        # PersistentObject is created too early in the import cycle and
        # basically makes it impossible to add. Just skip it.
        if name != 'PersistentObject':
            # Add all the cached methods and properties to the global function
            # map.

            def get_members(cls):
                return map(functools.partial(getattr, cls), dir(cls))

            all_members = itertools.chain(get_members(cls),
                                          *map(get_members, bases))

            for member in all_members:
                if isinstance(member, (cachemethod, cacheproperty)):
                    member.method.__fbuild_member_of__ = cls
                    _update_fun_map(member.method)

            _update_fun_map(cls.__call_super__)

    def __call_super__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

    def __call__(cls, ctx, *args, **kwargs):
        _check_ctx(ctx, cls.__name__, 'PersistentMeta.__call__')
        result, srcs, objs = ctx.db.call(cls.__call_super__, ctx,
            *args, **kwargs)

        return result


class PersistentObject(metaclass=PersistentMeta):
    """An abstract baseclass that will cache instances in the database."""

    def __init__(self, ctx):
        # No _check_ctx is needed because that's covered by
        # PersistentMeta.__call__.
        self.ctx = ctx

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, type(self)):
            return False

        # Step through the members and exit if they aren't equal.
        try:
            for key in self.__dict__:
                if getattr(self, key) != getattr(other, key):
                    return False
        except AttributeError:
            return False
        else:
            return True

# ------------------------------------------------------------------------------

class caches:
    """L{caches} decorates a function and caches the results.  The first
    argument of the function must be an instance of L{database}.

    >>> import fbuild.context
    >>> ctx = fbuild.context.make_default_context(['--database=cache'])
    >>> ctx.db.connect()
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
        _update_fun_map(function)
        functools.update_wrapper(self, function)
        self.function = function

    def __call__(self, *args, **kwargs):
        result, srcs, dsts = self.call(*args, **kwargs)
        return result

    def call(self, ctx, *args, **kwargs):
        _check_ctx(ctx, self.function.__name__, 'caches.call')
        return ctx.db.call(self.function, ctx, *args, **kwargs)


class cachemethod:
    """L{cachemethod} decorates a method of a class to cache the results.

    >>> import fbuild.context
    >>> ctx = fbuild.context.make_default_context(['--database=cache'])
    >>> ctx.db.connect()
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
        _check_ctx(self.method.__self__.ctx,
                   self.method.__self__.__class__.__name__,
                   'cache<member>.call')
        return self.method.__self__.ctx.db.call(self.method, *args, **kwargs)


class cacheproperty:
    """L{cacheproperty} acts like a normal I{property} but will memoize the
    result in the store.  The first argument of the function it wraps must be a
    store or a class that has has an attribute named I{store}.

    >>> import fbuild.context
    >>> import fbuild.db
    >>> ctx = fbuild.context.make_default_context(['--database=cache'])
    >>> ctx.db.connect()
    >>> class C(fbuild.db.PersistentObject):
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
        _check_ctx(instance.ctx, instance.__class__.__name__,
                   'cache<member>.call')
        return instance.ctx.db.call(types.MethodType(self.method, instance))
