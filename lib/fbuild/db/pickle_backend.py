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
        assert isinstance(fun_name, str), fun_name

        try:
            fun_digest = self._functions[fun_name]
        except KeyError:
            # This is the first time we've seen this function.
            fun_digest = None

        # The name is the id.
        return fun_name, fun_digest


    def save_function(self, fun_name, fun_digest):
        """Insert or update the function's digest."""

        # Make sure we have the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(fun_digest, str), fun_digest

        # Since the function changed, delete out all the related data.
        self.delete_function(fun_name)

        self._functions[fun_name] = fun_digest

        # The name is the id.
        return fun_name


    def delete_function(self, fun_name):
        """Clear the function from the database."""

        # Make sure we have the right types.
        assert isinstance(fun_name, str), fun_name

        function_existed = False
        try:
            del self._functions[fun_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        # Since the function was removed, all of this function's calls and call
        # files are dirty, so delete them.
        try:
            del self._function_calls[fun_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_srcs[fun_name]
        except KeyError:
            pass
        else:
            function_existed |= True

        try:
            del self._external_dsts[fun_name]
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
                del value[fun_name]
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
                function_existed |= True

        return function_existed

    # --------------------------------------------------------------------------

    def find_call(self, fun_id, bound):
        """Returns the function call index and result or None if it does not
        exist."""

        # Make sure we got the right types.
        assert isinstance(fun_id, str), fun_id
        assert isinstance(bound, dict), bound

        try:
            datas = self._function_calls[fun_id]
        except KeyError:
            # This is the first time we've seen this function.
            return True, (fun_id, None), None

        # We've called this before, so search the data to see if we've called
        # it with the same arguments.
        for call_index, (old_bound, old_result) in enumerate(datas):
            if bound == old_bound:
                # We've found a matching call so just return the index.
                return False, (fun_id, call_index), old_result

        # Turns out we haven't called it with these args.
        return True, (fun_id, None), None


    def save_call(self, call_id, fun_id, bound, result):
        """Insert or update the function call."""

        # Extract out the real fun_id and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, (type(None), int)), call_index
        assert isinstance(bound, dict), bound

        try:
            datas = self._function_calls[fun_name]
        except KeyError:
            # The function be new or may have been deleted. So ignore the
            # call_id and just create a new list.
            self._function_calls[fun_name] = [(bound, result)]

            call_index = 0
        else:
            if call_index is None:
                datas.append((bound, result))
                call_index = len(datas) - 1
            else:
                datas[call_index] = (bound, result)

        # The call_id is a tuple of the function name and the index into the
        # call array.
        return (fun_name, call_index)

    # --------------------------------------------------------------------------

    def find_call_file(self, call_id, file_name):
        """Returns the digest of the file from the last time we called this
        function, or None if it does not exist."""

        # Extract out the real fun_name and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, (type(None), int)), call_index
        assert isinstance(file_name, str), file_name

        try:
            return self._call_files[file_name][fun_name][call_index]
        except KeyError:
            # This is the first time we've seen this file with this call.
            return None


    def save_call_file(self, call_id, file_name, digest):
        """Insert or update the call file."""

        # Extract out the real fun_name and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, int), call_index
        assert isinstance(file_name, str), file_name
        assert isinstance(digest, str), digest

        self._call_files. \
            setdefault(file_name, {}).\
            setdefault(fun_name, {})[call_index] = digest

    # --------------------------------------------------------------------------

    def find_external_srcs(self, call_id):
        """Returns all of the externally specified call src files"""

        # Extract out the real fun_name and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, (type(None), int)), call_index

        try:
            return self._external_srcs[fun_name][call_index]
        except KeyError:
            return set()


    def find_external_dsts(self, call_id):
        """Returns all of the externally specified call dst files"""

        # Extract out the real fun_name and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, (type(None), int)), call_index

        try:
            return self._external_dsts[fun_name][call_index]
        except KeyError:
            return set()


    def save_external_files(self, call_id, srcs, dsts):
        """Insert or update the externall specified call files."""

        # Extract out the real fun_name and call_id
        fun_name, call_index = call_id

        # Make sure we got the right types.
        assert isinstance(fun_name, str), fun_name
        assert isinstance(call_index, int), call_index
        assert all(isinstance(src, str) for src in srcs), srcs
        assert all(isinstance(dst, str) for dst in dsts), dsts

        srcs = frozenset(srcs)
        dsts = frozenset(dsts)

        self._external_srcs.setdefault(fun_name, {})[call_index] = srcs
        self._external_dsts.setdefault(fun_name, {})[call_index] = dsts

        external_digests = []
        for src in srcs:
            dirty, file_id, mtime, digest = self.add_file(src)
            external_digests.append((file_id, digest))

        self.save_call_files(call_id, external_digests)

    # --------------------------------------------------------------------------

    def find_file(self, file_name):
        """Returns the mtime and digest of the file, or None if it does not
        exist."""

        # Make sure we got the right types.
        assert isinstance(file_name, str), file_name

        try:
            file_mtime, file_digest = self._files[file_name]
        except KeyError:
            file_mtime = None
            file_digest = None

        # We'll return the file_name as the file_id.
        return file_name, file_mtime, file_digest


    def save_file(self, file_name, file_mtime, file_digest):
        """Insert or update the file."""

        # Make sure we got the right types.
        assert isinstance(file_name, str), file_name
        assert isinstance(file_mtime, float), file_mtime
        assert isinstance(file_digest, str), file_digest

        self._files[file_name] = (file_mtime, file_digest)

        # We'll return the file_name as the file_id.
        return file_name


    def delete_file(self, file_name):
        """Remove the file from the database."""

        # Make sure we got the right types.
        assert isinstance(file_name, str), file_name

        file_existed = False
        try:
            del self._files[file_name]
        except KeyError:
            pass
        else:
            file_existed |= True

        # And delete all of the related call files.
        try:
            del self._call_files[file_name]
        except KeyError:
            pass
        else:
            file_existed |= True

        return file_existed
