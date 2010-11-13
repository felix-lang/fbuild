import io
import pickle
import time

import fbuild.path

# ------------------------------------------------------------------------------

class PickleBackend:
    def __init__(self, ctx):
        self._ctx = ctx
        self._functions = {}
        self._function_calls = {}
        self._files = {}
        self._call_files = {}
        self._external_srcs = {}
        self._external_dsts = {}

    def save(self, filename):
        """Save the database to the file."""

        f = io.BytesIO()
        pickler = _Pickler(self._ctx, f, pickle.HIGHEST_PROTOCOL)

        pickler.dump((
            self._functions,
            self._function_calls,
            self._files,
            self._call_files,
            self._external_srcs,
            self._external_dsts))

        s = f.getvalue()

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
        """Load the database from the file."""

        with open(filename, 'rb') as f:
            unpickler = _Unpickler(self._ctx, f)

            self._functions, self._function_calls, self._files, \
                self._call_files, self._external_srcs, \
                self._external_dsts = unpickler.load()

    def prepare(self,
            function_name,
            function_digest,
            bound,
            srcs,
            dsts):
        """Queries all the information needed to cache a function."""

        # Check if the function changed.
        function_dirty = self.check_function(function_name, function_digest)

        # Check if this is a new call and get the index.
        call_id, old_result = self.find_call(function_name, bound)

        # Add the source files to the database.
        call_file_digests = self.check_call_files(call_id, function_name, srcs)

        # Check extra external call files.
        external_dirty, external_srcs, external_dsts, external_digests = \
            self.check_external_files(function_name, call_id)

        return (
            function_dirty,
            call_id,
            old_result,
            call_file_digests,
            external_dirty,
            external_srcs,
            external_dsts,
            external_digests)

    def cache(self,
            function_dirty,
            function_name,
            function_digest,
            call_id,
            bound,
            result,
            call_file_digests,
            external_srcs,
            external_dsts,
            external_digests):
        """Saves the function call into the database."""

        # Lock the db since we're updating data structures.
        if function_dirty:
            self.save_function(function_name, function_digest)

        # Get the real call_id to use in the call files.
        call_id = self.save_call(function_name, call_id, bound, result)

        self.save_call_files(call_id, function_name, call_file_digests)

        self.save_external_files(
            function_name,
            call_id,
            external_srcs,
            external_dsts,
            external_digests)

    # --------------------------------------------------------------------------

    def find_function(self, function_name):
        """Returns the function record or None if it does not exist."""

        # Make sure we got the right types.
        assert isinstance(function_name, str)

        try:
            return self._functions[function_name]
        except KeyError:
            # This is the first time we've seen this function.
            return None


    def check_function(self, function_name, function_digest):
        """Returns whether or not the function is dirty. Returns True or false
        as well as the function's digest."""

        # Make sure we got the right types.
        assert isinstance(function_name, str)
        assert isinstance(function_digest, str)

        old_digest = self.find_function(function_name)

        # Check if the function changed. If it didn't, assume that the function
        # didn't change either (although any sub-functions could have).
        return old_digest is None or function_digest != old_digest


    def save_function(self, function_name, digest):
        """Insert or update the function's digest."""

        # Make sure we got the right types.
        assert isinstance(function_name, str)
        assert isinstance(digest, str)

        # Since the function changed, clear out all the related data.
        self.clear_function(function_name)

        self._functions[function_name] = digest


    def clear_function(self, function_name):
        """Clear the function from the database."""

        # Make sure we got the right types.
        assert isinstance(function_name, str)

        function_existed = False
        try:
            del self._functions[function_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        # Since the function was removed, all of this function's
        # calls are dirty, so delete them.
        try:
            del self._function_calls[function_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_srcs[function_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_dsts[function_name]
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
                del value[function_name]
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

    def find_call(self, function, bound):
        """Returns the function call index and result or None if it does not
        exist."""

        # Make sure we got the right types.
        assert isinstance(function, str)
        assert isinstance(bound, dict)

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


    def save_call(self, function_name, call_id, bound, result):
        """Insert or update the function call."""

        # Make sure we got the right types.
        assert isinstance(call_id, (type(None), int))
        assert isinstance(function_name, str)
        assert isinstance(bound, dict)

        try:
            datas = self._function_calls[function_name]
        except KeyError:
            # The function be new or may have been cleared. So ignore the
            # call_id and just create a new list.
            self._function_calls[function_name] = [(bound, result)]
            return 0
        else:
            if call_id is None:
                datas.append((bound, result))
                return len(datas) - 1
            else:
                datas[call_id] = (bound, result)
        return call_id

    # --------------------------------------------------------------------------

    def check_external_files(self, call_id, function_name):
        """Returns all of the externally specified call files, and the dirty
        list."""

        # Make sure we got the right types.
        assert isinstance(call_id, (type(None), int))
        assert isinstance(function_name, str)

        external_dirty = False
        digests = []
        try:
            srcs = self._external_srcs[function_name][call_id]
        except KeyError:
            srcs = set()
        else:
            for src in srcs:
                try:
                    d, digest = self.check_call_file(
                        call_id,
                        function_name,
                        src)
                except OSError:
                    external_dirty = True
                else:
                    if d:
                        digests.append((src, digest))

        try:
            dsts = self._external_dsts[function_name][call_id]
        except KeyError:
            dsts = set()

        return external_dirty, srcs, dsts, digests

    def save_external_files(self,
            function_name,
            call_id,
            srcs,
            dsts,
            digests):
        """Insert or update the externall specified call files."""

        # Make sure we got the right types.
        assert isinstance(call_id, int)
        assert isinstance(function_name, str)
        assert all(isinstance(src, str) for src in srcs)
        assert all(isinstance(dst, str) for dst in dsts)
        assert all(isinstance(src, str) and isinstance(digest, str)
            for src, digest in digests)

        self._external_srcs.setdefault(function_name, {})[call_id] = srcs
        self._external_dsts.setdefault(function_name, {})[call_id] = dsts

        for src, digest in digests:
            self.save_call_file(call_id, function_name, src, digest)

    # --------------------------------------------------------------------------

    def check_call_files(self, call_id, function_name, filenames):
        """Returns all of the dirty call files."""

        # Make sure we got the right types.
        assert isinstance(call_id, (type(None), int))
        assert isinstance(function_name, str)

        digests = []
        for filename in filenames:
            d, digest = self.check_call_file(call_id, function_name, filename)
            if d:
                digests.append((filename, digest))

        return digests

    def save_call_files(self, call_id, function_name, digests):
        """Insert or update the call files."""

        # Make sure we got the right types.
        assert isinstance(call_id, int)
        assert isinstance(function_name, str)

        for src, digest in digests:
            self.save_call_file(call_id, function_name, src, digest)

    # --------------------------------------------------------------------------

    def check_call_file(self, call_id, function_name, filename):
        """Returns if the call file is dirty and the file's digest."""

        # Compute the digest of the file.
        dirty, (mtime, digest) = self.add_file(filename)

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
            old_digest = datas[function_name][call_id]
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

    def save_call_file(self, call_id, function_name, filename, digest):
        """Insert or update the call file."""

        # Make sure we got the right types.
        assert isinstance(call_id, int)
        assert isinstance(function_name, str)
        assert isinstance(filename, str)
        assert isinstance(digest, str)

        self._call_files. \
            setdefault(filename, {}).\
            setdefault(function_name, {})[call_id] = digest

    # --------------------------------------------------------------------------

    def add_file(self, filename):
        """Insert or update the file information. Returns True if the content
        of the file is different from what was in the table."""

        # Make sure we got the right types.
        assert isinstance(filename, str)

        mtime = fbuild.path.Path(filename).getmtime()
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

        # Since the function changed, all of the calls that used this
        # function are dirty.
        self.clear_file(filename)

        # Now, add the file back to the database.
        data = self._files[filename] = (mtime, digest)

        # Returns True since the file changed.
        return True, data


    def clear_file(self, filename):
        """Remove the file from the database."""
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

# ------------------------------------------------------------------------------

class _Pickler(pickle._Pickler):
    """Create a custom pickler that won't try to pickle the context."""

    def __init__(self, ctx, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx

    def persistent_id(self, obj):
        if obj is self.ctx:
            return 'ctx'
        else:
            return None

class _Unpickler(pickle._Unpickler):
    """Create a custom unpickler that will substitute the current context."""

    def __init__(self, ctx, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx = ctx

    def persistent_load(self, pid):
        if pid == 'ctx':
            return self.ctx
        else:
            raise pickle.UnpicklingError('unsupported persistent object')
