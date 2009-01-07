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
        self._lock = threading.RLock()
        self._function_locks = {}

    def save(self, filename):
        s = pickle.dumps((
            self._functions,
            self._function_calls,
            self._files,
            self._call_files))

        with open(filename, 'wb') as f:
            f.write(s)

    def load(self, filename):
        with open(filename, 'rb') as f:
            self._functions, self._function_calls, self._files, \
                self._call_files = pickle.load(f)

    def call(self, function, *args, **kwargs):
        """Call the function and return the result. If the function has been
        previously called with the same arguments, return the cached results.
        If we detect that the function changed, throw away all the cached
        values for that function. Similarly, throw away all of the cached
        values if any of the optionally specified "srcs" are also modified.
        Finally, if any of the filenames in "dsts" do not exist, re-run the
        function no matter what."""
        return self.call_with_dependencies(function, args, kwargs)

    def call_with_dependencies(self, function, args, kwargs, *,
            srcs=(),
            dsts=(),
            return_type=None):
        if not fbuild.inspect.ismethod(function):
            function_name = function.__module__ + '.' + function.__name__
        else:
            function_name = '%s.%s.%s' % (
                function.__module__,
                function.__self__.__class__.__name__,
                function.__name__)
            args = (function.__self__,) + args
            function = function.__func__

        # Bind the arguments so that we can look up normal args by name.
        bound = fbuild.functools.bind_args(function, args, kwargs)

        # Check if any of the files changed.
        return_type = None
        srcs = list(srcs)
        dsts = list(dsts)
        for akey, avalue in function.__annotations__.items():
            if akey == 'return':
                return_type = avalue
            elif issubclass(avalue, SRC):
                srcs.extend(avalue.convert(bound[akey]))
            elif issubclass(avalue, DST):
                srcs.extend(avalue.convert(bound[akey]))

        # Get or create the function-level lock.
        with self._lock:
            try:
                function_lock = self._function_locks[function_name]
            except KeyError:
                function_lock = self._function_locks[function_name] = \
                        threading.RLock()

        with function_lock:
            return self._cache(function_name, function, args, kwargs, bound,
                srcs=srcs,
                dsts=dsts,
                return_type=return_type)

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

    def _cache(self, function_name, function, args, kwargs, bound, *,
            srcs=(),
            dsts=(),
            return_type=None):
        # Make sure none of the arguments are a generator.
        for arg in itertools.chain(args, kwargs.values()):
            assert not fbuild.inspect.isgenerator(arg), \
                "Cannot store generator in database"

        # Check if the function changed.
        dirty = self._add_function(function, function_name)

        # Check if this is a new call and get the index.
        d, call_id = self._add_call(function_name, bound)
        dirty |= d

        # Add the source files to the database.
        for src in srcs:
            dirty |= self._add_call_file(src, function_name, call_id)

        # Check if we have a result. If not, then we're dirty.
        try:
            old_result = self._function_calls[function_name][call_id][1]
        except LookupError:
            dirty = True
        else:
            # Don't try to check return type if it's an exception.
            if not isinstance(old_result, fbuild.Error):
                # If the result is a dst filename, make sure it exists. If not,
                # we're dirty.
                dsts = list(dsts)
                if return_type is not None and issubclass(return_type, DST):
                    dsts.extend(return_type.convert(old_result))

                for dst in dsts:
                    if not fbuild.path.Path.exists(dst):
                        dirty = True
                        break

            if not dirty:
                # If the old_result was an exception, raise it.
                if isinstance(old_result, fbuild.Error):
                    raise old_result from old_result

                # The call was not dirty, so return the cached value.
                return old_result

        # The call was dirty, so recompute it.
        try:
            result = function(*args, **kwargs)
        except fbuild.Error as e:
            result = e
        else:
            # Make sure the result is not a generator.
            assert not fbuild.inspect.isgenerator(result), \
                "Cannot store generator in database"

        self._function_calls[function_name][call_id] = (bound, result)

        # If the result was an exception, raise it.
        if isinstance(result, fbuild.Error):
            raise result from result

        return result

    # Create an in-process cache of the function digests, since they shouldn't
    # change while we're running.
    _digest_function_cache = {}
    def _digest_function(self, function):
        """Compute the digest for a function or a function object. Cache this
        for this instance."""
        try:
            digest = self._digest_function_cache[function]
        except KeyError:
            if fbuild.inspect.isroutine(function):
                # The function is a function, method, or lambda, so digest the
                # source. If the function is a builtin, we will raise an
                # exception.
                src = fbuild.inspect.getsource(function)
                digest = hashlib.md5(src.encode()).hexdigest()
            else:
                # The function is a functor so let it digest itself.
                digest = hash(function)
            self._digest_function_cache[function] = digest

        return digest

    def _add_function(self, function, name):
        """Insert or update the function information. Returns True if the
        function changed."""
        digest = self._digest_function(function)
        try:
            old_digest = self._functions[name]
        except KeyError:
            # This is the first time we've seen this function, so store it and
            # return True.
            self._functions[name] = digest
            return True

        # Check if the function changed. If it didn't, assume that the function
        # didn't change either (although any sub-functions could have).
        if digest == old_digest:
            return False

        # Since the function changed, clear out all the related data.
        self.clear_function(name)

        # Update the table with the new digest.
        self._functions[name] = digest

        return True

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

    def _add_call(self, function, bound):
        """Insert functon call information. Returns True if the function was
        actually inserted and the index that it was inserted at."""
        try:
            datas = self._function_calls[function]
        except KeyError:
            # This is the first time we've seen this function, so store it and
            # return True.
            self._function_calls[function] = [(bound,)]
            return True, 0

        # We've called this before, so search the data to see if we've called
        # it with the same arguments.
        for index, data in enumerate(datas):
            if bound == data[0]:
                # We've found a matching call so just return it.
                return False, index

        # Turns out we haven't called it with these args, so just append it.
        datas.append((bound,))
        return True, len(datas) - 1

    # --------------------------------------------------------------------------

    def _add_call_file(self, filename, function, call_id):
        """Insert or update file information for a call. Returns True if the
        file was actually inserted or updated."""
        # Compute the digest of the file.
        dirty, (mtime, digest) = self._add_file(filename)

        try:
            datas = self._call_files[filename]
        except KeyError:
            # This is the first time we've seen this call, so store it and
            # return True.
            self._call_files[filename] = {function: {call_id: digest}}
            return True

        # We've called this before, lets see if we can find the file.
        try:
            old_digest = datas[function][call_id]
        except KeyError:
            # This is the first time we've seen this file, so store it and
            # return True.
            datas.setdefault(function, {})[call_id] = digest
            return True

        # Now, check if the file changed from the previous run. If it did then
        # return True.
        if digest == old_digest:
            # We're okay, so return if the file's been updated.
            return dirty
        else:
            # The digest's different, so we're dirty.
            datas.setdefault(function, {})[call_id] = digest
            return True

    # --------------------------------------------------------------------------

    def _add_file(self, filename):
        """Insert or update the file information. Returns True if the content
        of the file is different from what was in the table."""
        mtime = fbuild.path.Path.getmtime(filename)
        try:
            data = old_mtime, old_digest = self._files[filename]
        except KeyError:
            # This is the first time we've seen this file, so store it in the
            # table and return that this is new data.
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

        # If the file's contents didn't change, just return.
        if digest == old_digest:
            # The timestamp did change, so update the row.
            self._files[filename] = (mtime, old_digest)
            return False, data

        # Since the function changed, all of the calls that used this function
        # are dirty.
        self.clear_file(filename)

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
        return database.call(cls.__call_super__, *args, **kwargs)

class PersistentObject(metaclass=PersistentMeta):
    """An abstract baseclass that will cache instances in the database."""

# ------------------------------------------------------------------------------

class caches:
    """L{caches} decorates a function and caches the results.  The first
    argument of the function must be an instance of L{database}."""

    def __init__(self, function):
        functools.update_wrapper(self, function)
        self.function = function

    def __call__(self, *args, **kwargs):
        return database.call(self.function, *args, **kwargs)

    def call_with_dependencies(self, *args, **kwargs):
        return database.call_with_dependencies(self.function, *args, **kwargs)

class cachemethod:
    """L{cachemethod} decorates a method of a class to cache the results."""
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
        return database.call(self.method, *args, **kwargs)

    def call_with_dependencies(self, *args, **kwargs):
        return database.call_with_dependencies(self.method, *args, **kwargs)
