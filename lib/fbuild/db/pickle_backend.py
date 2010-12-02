import io
import pickle

import fbuild.db.backend
import fbuild.path

# ------------------------------------------------------------------------------

class PickleBackend(fbuild.db.backend.Backend):
    def connect(self, filename):
        """Load the database from the file."""

        self._file_name = fbuild.path.Path(filename)

        if self._file_name.exists():
            with open(self._file_name, 'rb') as f:
                unpickler = fbuild.db.backend.Unpickler(self._ctx, f)

                self._functions, self._function_calls, self._files, \
                    self._call_files, self._external_srcs, \
                    self._external_dsts = unpickler.load()
        else:
            self._functions = {}
            self._function_calls = {}
            self._files = {}
            self._call_files = {}
            self._external_srcs = {}
            self._external_dsts = {}


    def close(self):
        """Save the database to the file."""

        f = io.BytesIO()
        pickler = fbuild.db.backend.Pickler(self._ctx, f)

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
        path = fbuild.path.Path(self._file_name)
        tmp = path + '.tmp'
        old = path + '.old'

        with open(tmp, 'wb') as f:
            f.write(s)

        if path.exists():
            path.rename(old)

        tmp.rename(path)

        if old.exists():
            old.remove()

    # --------------------------------------------------------------------------

    def find_function(self, fun_name):
        """Returns the function record or None if it does not exist."""

        # Make sure we got the right types.
        assert isinstance(fun_name, str)

        try:
            return fun_name, self._functions[fun_name]
        except KeyError:
            # This is the first time we've seen this function. We'll use the
            # function name as it's id.
            return fun_name, None


    def save_function(self, fun_id, fun_name, digest):
        """Insert or update the function's digest."""

        assert isinstance(fun_id, str), fun_id
        assert isinstance(fun_name, str), fun_name
        assert isinstance(digest, str), digest

        # Since the function changed, delete out all the related data.
        self.delete_function(fun_id)

        self._functions[fun_id] = digest

        return fun_id


    def delete_function(self, fun_name):
        """Clear the function from the database."""

        # Make sure we got the right types.
        assert isinstance(fun_name, str)

        try:
            del self._functions[fun_name]
        except KeyError:
            pass

        # Since the function was removed, all of this function's calls and call
        # files are dirty, so delete them.
        try:
            del self._function_calls[fun_name]
        except KeyError:
            pass

        try:
            del self._external_srcs[fun_name]
        except KeyError:
            pass

        try:
            del self._external_dsts[fun_name]
        except KeyError:
            pass

        # Since _call_files is indexed by filename, we need to search through
        # each item and delete any references to this function. The assumption
        # is that the files will change much less frequently compared to
        # functions, so we can have this be a more expensive call.
        remove_keys = []
        for key, value in self._call_files.items():
            try:
                del value[fun_name]
            except KeyError:
                pass

            if not value:
                remove_keys.append(key)

        # If any of the _call_files have no values, remove them.
        for key in remove_keys:
            try:
                del self._call_files[key]
            except KeyError:
                pass

    # --------------------------------------------------------------------------

    def find_call(self, fun_id, bound):
        """Returns the function call index and result or None if it does not
        exist."""

        # Make sure we got the right types.
        assert isinstance(fun_id, str)
        assert isinstance(bound, dict)

        try:
            datas = self._function_calls[fun_id]
        except KeyError:
            # This is the first time we've seen this function.
            return None, None

        # We've called this before, so search the data to see if we've called
        # it with the same arguments.
        for call_id, (old_bound, old_result) in enumerate(datas):
            if bound == old_bound:
                # We've found a matching call so just return the index.
                return call_id, old_result

        # Turns out we haven't called it with these args.
        return None, None


    def save_call(self, fun_id, call_id, bound, result):
        """Insert or update the function call."""

        # Make sure we got the right types.
        assert isinstance(call_id, (type(None), int))
        assert isinstance(fun_id, str)
        assert isinstance(bound, dict)

        try:
            datas = self._function_calls[fun_id]
        except KeyError:
            # The function be new or may have been deleted. So ignore the
            # call_id and just create a new list.
            self._function_calls[fun_id] = [(bound, result)]
            return 0
        else:
            if call_id is None:
                datas.append((bound, result))
                return len(datas) - 1
            else:
                datas[call_id] = (bound, result)
        return call_id

    # --------------------------------------------------------------------------

    def find_call_file(self, call_id, fun_id, file_id):
        """Returns the digest of the file from the last time we called this
        function, or None if it does not exist."""

        try:
            return self._call_files[file_id][fun_id][call_id]
        except KeyError:
            # This is the first time we've seen this file with this call.
            return None


    def save_call_file(self, call_id, fun_id, file_id, digest):
        """Insert or update the call file."""

        # Make sure we got the right types.
        assert isinstance(call_id, int), call_id
        assert isinstance(fun_id, str), fun_id
        assert isinstance(file_id, str), file_id
        assert isinstance(digest, str), digest

        self._call_files. \
            setdefault(file_id, {}).\
            setdefault(fun_id, {})[call_id] = digest

    # --------------------------------------------------------------------------

    def find_external_srcs(self, call_id, fun_id):
        """Returns all of the externally specified call src files"""

        try:
            return self._external_srcs[fun_id][call_id]
        except KeyError:
            return set()


    def find_external_dsts(self, call_id, fun_id):
        """Returns all of the externally specified call dst files"""

        try:
            return self._external_dsts[fun_id][call_id]
        except KeyError:
            return set()


    def save_external_files(self, fun_id, call_id, srcs, dsts, digests):
        """Insert or update the externall specified call files."""

        # Make sure we got the right types.
        assert isinstance(call_id, int)
        assert isinstance(fun_id, str)
        assert all(isinstance(src, str) for src in srcs)
        assert all(isinstance(dst, str) for dst in dsts)
        assert all(isinstance(src, str) and isinstance(digest, str)
            for src, digest in digests)

        self._external_srcs.setdefault(fun_id, {})[call_id] = srcs
        self._external_dsts.setdefault(fun_id, {})[call_id] = dsts

        self.save_call_files(call_id, fun_id, digests)

    # --------------------------------------------------------------------------

    def find_file(self, file_name):
        """Returns the mtime and digest of the file, or None if it does not
        exist."""

        try:
            mtime, digest = self._files[file_name]
        except KeyError:
            return None, None, None
        else:
            # Return the file's name as it's id for now.
            return file_name, mtime, digest


    def save_file(self, file_name, mtime, digest):
        """Insert or update the file."""

        # Make sure we got the right types.
        assert isinstance(file_name, str)
        assert isinstance(mtime, float)
        assert isinstance(digest, str)

        self._files[file_name] = (mtime, digest)

        # Return the file's name as it's id for now.
        return file_name


    def delete_file(self, file_name):
        """Remove the file from the database."""

        try:
            del self._files[file_name]
        except KeyError:
            pass

        # And delete all of the related call files.
        try:
            del self._call_files[file_name]
        except KeyError:
            pass
