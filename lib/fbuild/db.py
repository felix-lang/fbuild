import abc
import functools
import hashlib
import itertools
import pickle
import time
import threading
import types

import fbuild
import fbuild.functools
import fbuild.inspect
import fbuild.path

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

    def __init__(self):
        self._functions = {}
        self._function_calls = {}
        self._files = {}
        self._call_files = {}
        self._external_srcs = {}
        self._external_dsts = {}
        self._lock = threading.RLock()

    def save(self, filename):
        with self._lock:
            s = pickle.dumps((
                self._functions,
                self._function_calls,
                self._files,
                self._call_files,
                self._external_srcs,
                self._external_dsts))

        # Try to save the state as atomically as possible. Unfortunately, if
        # someone presses ctrl+c while we're saving, we might corrupt the db.
        # So, we'll write to a temp file, then move the old state file out of
        # the way, then rename the temp file to the filename.
        path = fbuild.path.Path(filename)
        tmp = path + '.tmp'
        old = path + '.old'

        with open(tmp, 'wb') as f:
            f.write(s)

        if path.exists():
            path.rename(old)

        tmp.rename(path)

        if old.exists():
            old.remove()

    def load(self, filename):
        with self._lock:
            with open(filename, 'rb') as f:
                self._functions, self._function_calls, self._files, \
                    self._call_files, self._external_srcs, \
                    self._external_dsts = pickle.load(f)

    def call(self, function, *args, **kwargs):
        """Call the function and return the result, src dependencies, and dst
        dependencies. If the function has been previously called with the same
        arguments, return the cached results.  If we detect that the function
        changed, throw away all the cached values for that function. Similarly,
        throw away all of the cached values if any of the optionally specified
        "srcs" are also modified.  Finally, if any of the filenames in "dsts"
        do not exist, re-run the function no matter what."""
        if not fbuild.inspect.ismethod(function):
            function_name = function.__module__ + '.' + function.__name__
        else:
            function_name = '%s.%s.%s' % (
                function.__module__,
                function.__self__.__class__.__name__,
                function.__name__)
            args = (function.__self__,) + args
            function = function.__func__

        if not fbuild.inspect.isroutine(function):
            function = function.__call__

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

        return self._cache(function_name, function, args, kwargs, bound,
            srcs, dsts, return_type)

    def clear_function(self, function):
        """Remove the function name from the database."""
        # This is a simple wrapper in order to grab the lock.
        with self._lock:
            return self._clear_function(function)

    def clear_file(self, filename):
        """Remove the file from the database."""
        # This is a simple wrapper in order to grab the lock.
        with self._lock:
            return self._clear_file(filename)

    # --------------------------------------------------------------------------

    def _cache(self, function_name, function, args, kwargs, bound, srcs, dsts,
            return_type):
        # Make sure none of the arguments are a generator.
        for arg in itertools.chain(args, kwargs.values()):
            assert not fbuild.inspect.isgenerator(arg), \
                "Cannot store generator in database"

        with self._lock:
            # Check if the function changed.
            function_dirty, function_digest = \
                self._check_function(function, function_name)

            # Check if this is a new call and get the index.
            call_id, old_result = self._check_call(function_name, bound)

            # Add the source files to the database.
            call_file_digests = \
                self._check_call_files(srcs, function_name, call_id)

            # Check extra external call files.
            external_srcs, external_dsts, external_digests = \
                self._check_external_files(function_name, call_id)

        # Check if we have a result. If not, then we're dirty.
        if not (function_dirty or \
                call_id is None or \
                call_file_digests or \
                external_digests):
            # If the result is a dst filename, make sure it exists. If not,
            # we're dirty.
            if return_type is not None and issubclass(return_type, DST):
                return_dsts = return_type.convert(old_result)
            else:
                return_dsts = ()

            for dst in itertools.chain(return_dsts, dsts, external_dsts):
                if not fbuild.path.Path(dst).exists():
                    break
            else:
                # The call was not dirty, so return the cached value.
                all_srcs = srcs.union(external_srcs)
                all_dsts = dsts.union(external_dsts)
                all_dsts.update(return_dsts)
                return old_result, all_srcs, all_dsts

        # The call was dirty, so recompute it.
        result = function(*args, **kwargs)

        # Make sure the result is not a generator.
        assert not fbuild.inspect.isgenerator(result), \
            "Cannot store generator in database"

        # Lock the db since we're updating data structures.
        with self._lock:
            if function_dirty:
                self._update_function(function_name, function_digest)

            if call_id is None:
                # Get the real call_id to use in the call files.
                call_id = self._update_call(
                    function_name, call_id, bound, result)

            self._update_call_files(call_file_digests, function_name, call_id)
            self._update_external_files(function_name, call_id,
                external_srcs,
                external_dsts,
                external_digests)

        if return_type is not None and issubclass(return_type, DST):
            return_dsts = return_type.convert(result)
        else:
            return_dsts = ()

        all_srcs = srcs.union(external_srcs)
        all_dsts = dsts.union(external_dsts)
        all_dsts.update(return_dsts)
        return result, all_srcs, all_dsts

    # Create an in-process cache of the function digests, since they shouldn't
    # change while we're running.
    _digest_function_lock = threading.Lock()
    _digest_function_cache = {}
    def _digest_function(self, function):
        """Compute the digest for a function or a function object. Cache this
        for this instance."""
        with self._digest_function_lock:
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

    def _check_function(self, function, name):
        """Returns whether or not the function is dirty. Returns True or false
        as well as the function's digest."""
        digest = self._digest_function(function)
        try:
            old_digest = self._functions[name]
        except KeyError:
            # This is the first time we've seen this function.
            return True, digest

        # Check if the function changed. If it didn't, assume that the function
        # didn't change either (although any sub-functions could have).
        if digest == old_digest:
            return False, digest

        return True, digest

    def _update_function(self, function, digest):
        """Insert or update the function's digest."""
        # Since the function changed, clear out all the related data.
        self.clear_function(function)

        self._functions[function] = digest

    def _clear_function(self, name):
        """Actually clear the function from the database."""
        function_existed = False
        try:
            del self._functions[name]
        except KeyError:
            pass
        else:
            function_existed |= True

        # Since the function was removed, all of this function's
        # calls are dirty, so delete them.
        try:
            del self._function_calls[name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_srcs[name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_dsts[name]
        except KeyError:
            pass
        else:
            function_existed |= True

        # Since _call_files is indexed by filename, we need to search through
        # each item and delete any references to this function. The assumption
        # is that the files will change much less frequently compared to
        # functions, so we can have this be a more expensive call.
        remove_keys = []
        for key, value in self._call_files.items():
            try:
                del value[name]
            except KeyError:
                pass
            else:
                function_existed |= True

            if not value:
                remove_keys.append(key)

        # If any of the _call_files have no values, remove them.
        for key in remove_keys:
            try:
                del self._call_files[key]
            except KeyError:
                pass
            else:
                function_existed = True

        return function_existed

    # --------------------------------------------------------------------------

    def _check_call(self, function, bound):
        """Check if the function has been called before. Return the index if
        the call was cached, or None."""
        try:
            datas = self._function_calls[function]
        except KeyError:
            # This is the first time we've seen this function.
            return None, None

        # We've called this before, so search the data to see if we've called
        # it with the same arguments.
        for index, (old_bound, result) in enumerate(datas):
            if bound == old_bound:
                # We've found a matching call so just return the index.
                return index, result

        # Turns out we haven't called it with these args.
        return None, None

    def _update_call(self, function, call_id, bound, result):
        """Insert or update the function call."""
        try:
            datas = self._function_calls[function]
        except KeyError:
            assert call_id is None
            self._function_calls[function] = [(bound, result)]
            return 0
        else:
            if call_id is None:
                datas.append((bound, result))
                return len(datas) - 1
            else:
                datas[call_id] = (bound, result)
        return call_id

    # --------------------------------------------------------------------------

    def _check_call_files(self, filenames, function, call_id):
        """Returns all of the dirty call files."""
        digests = []
        for filename in filenames:
            d, digest = self._check_call_file(filename, function, call_id)
            if d:
                digests.append((filename, digest))

        return digests

    def _update_call_files(self, digests, function, call_id):
        """Insert or update the call files."""
        for src, digest in digests:
            self._update_call_file(src, function, call_id, digest)

    # --------------------------------------------------------------------------

    def _check_external_files(self, function, call_id):
        """Returns all of the externally specified call files, and the dirty
        list."""
        digests = []
        try:
            srcs = self._external_srcs[function][call_id]
        except KeyError:
            srcs = set()
        else:
            for src in srcs:
                d, digest = self._check_call_file(src, function, call_id)
                if d:
                    digests.append((src, digest))

        try:
            dsts = self._external_dsts[function][call_id]
        except KeyError:
            dsts = set()

        return srcs, dsts, digests

    def _update_external_files(self, function, call_id, srcs, dsts, digests):
        """Insert or update the externall specified call files."""
        self._external_srcs.setdefault(function, {})[call_id] = srcs
        self._external_dsts.setdefault(function, {})[call_id] = dsts

        for src, digest in digests:
            self._update_call_file(src, function, call_id, digest)

    # --------------------------------------------------------------------------

    def _check_call_file(self, filename, function, call_id):
        """Returns if the call file is dirty and the file's digest."""
        # Compute the digest of the file.
        dirty, (mtime, digest) = self._add_file(filename)

        # If we don't have a valid call_id, then it's a new call.
        if call_id is None:
            return True, digest

        try:
            datas = self._call_files[filename]
        except KeyError:
            # This is the first time we've seen this call, so store it and
            # return True.
            return True, digest

        # We've called this before, lets see if we can find the file.
        try:
            old_digest = datas[function][call_id]
        except KeyError:
            # This is the first time we've seen this file, so store it and
            # return True.
            return True, digest

        # Now, check if the file changed from the previous run. If it did then
        # return True.
        if digest == old_digest:
            # We're okay, so return if the file's been updated.
            return dirty, digest
        else:
            # The digest's different, so we're dirty.
            return True, digest

    def _update_call_file(self, filename, function, call_id, digest):
        """Insert or update the call file."""
        self._call_files. \
            setdefault(filename, {}).\
            setdefault(function, {})[call_id] = digest

    # --------------------------------------------------------------------------

    def _add_file(self, filename):
        """Insert or update the file information. Returns True if the content
        of the file is different from what was in the table."""
        mtime = fbuild.path.Path(filename).getmtime()
        try:
            data = old_mtime, old_digest = self._files[filename]
        except KeyError:
            # This is the first time we've seen this file, so store it in the
            # table and return that this is new data.
            with self._lock:
                data = self._files[filename] = (
                    mtime,
                    fbuild.path.Path.digest(filename))
            return True, data

        # If the file was modified less than 1.0 seconds ago, recompute the
        # hash since it still could have changed even with the same mtime. If
        # True, then assume the file has not been modified.
        if mtime == old_mtime and time.time() - mtime > 1.0:
            return False, data

        # The mtime changed, but maybe the content didn't.
        digest = fbuild.path.Path.digest(filename)

        with self._lock:
            # If the file's contents didn't change, just return.
            if digest == old_digest:
                # The timestamp did change, so update the row.
                self._files[filename] = (mtime, old_digest)
                return False, data

            # Since the function changed, all of the calls that used this
            # function are dirty.
            self._clear_file(filename)

            # Now, add the file back to the database.
            data = self._files[filename] = (mtime, digest)

        # Returns True since the file changed.
        return True, data

    # --------------------------------------------------------------------------

    def _clear_file(self, filename):
        """Actually clear the file from the database."""
        file_existed = False
        try:
            del self._files[filename]
        except KeyError:
            pass
        else:
            file_existed |= True

        # And clear all of the related call files.
        try:
            del self._call_files[filename]
        except KeyError:
            pass
        else:
            file_existed |= True

        return file_existed

# Instantiate a global instance
database = Database()

# ------------------------------------------------------------------------------

class PersistentMeta(abc.ABCMeta):
    """A metaclass that searches the db for an already instantiated class with
    the same arguments.  It subclasses from ABCMeta so that subclasses can
    implement abstract methods."""
    def __call_super__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        result, srcs, objs = database.call(cls.__call_super__, *args, **kwargs)
        return result

class PersistentObject(metaclass=PersistentMeta):
    """An abstract baseclass that will cache instances in the database."""

# ------------------------------------------------------------------------------

class caches:
    """L{caches} decorates a function and caches the results.  The first
    argument of the function must be an instance of L{database}.

    >>> @caches
    ... def test():
    ...     print('running test')
    ...     return 5
    >>> test()
    running test
    5
    >>> test()
    5
    """

    def __init__(self, function):
        functools.update_wrapper(self, function)
        self.function = function

    def __call__(self, *args, **kwargs):
        result, srcs, dsts = self.call(*args, **kwargs)
        return result

    def call(self, *args, **kwargs):
        return database.call(self.function, *args, **kwargs)

class cachemethod:
    """L{cachemethod} decorates a method of a class to cache the results.

    >>> class C:
    ...     @cachemethod
    ...     def test(self):
    ...         print('running test')
    ...         return 5
    >>> c = C()
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
        return database.call(self.method, *args, **kwargs)

class cacheproperty:
    """L{cacheproperty} acts like a normal I{property} but will memoize the
    result in the store.  The first argument of the function it wraps must be a
    store or a class that has has an attribute named I{store}.

    >>> class C:
    ...     @cacheproperty
    ...     def test(self):
    ...         print('running test')
    ...         return 5
    >>> c = C()
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
        return database.call(types.MethodType(self.method, instance))

# ------------------------------------------------------------------------------

def add_external_dependencies_to_call(*, srcs=(), dsts=()):
    """When inside a cached method, register additional src dependencies for
    the call. This function can only be called from a cached function and will
    error out if it is called from an uncached function."""
    # Hack in additional dependencies
    i = 2
    while True:
        frame = fbuild.inspect.currentframe(i)
        try:
            if frame.f_code == database._cache.__code__:
                function_name = frame.f_locals['function_name']
                call_id = frame.f_locals['call_id']
                external_digests = frame.f_locals['external_digests']
                external_srcs = frame.f_locals['external_srcs']
                external_dsts = frame.f_locals['external_dsts']

                for src in srcs:
                    external_srcs.add(src)
                    dirty, digest = database._check_call_file(
                        src, function_name, call_id)
                    if dirty:
                        external_digests.append((src, digest))

                external_dsts.update(dsts)

                return
            else:
                i += 1
        finally:
            del frame
