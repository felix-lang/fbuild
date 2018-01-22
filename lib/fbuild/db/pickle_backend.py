import io
import pickle

import fbuild.db.cache_backend
import fbuild.path

# ------------------------------------------------------------------------------

class PickleBackend(fbuild.db.cache_backend.CacheBackend):
    _LATEST_VERSION = '2'

    def _connect(self, filename):
        """Load the database from the file."""

        self._file_name = fbuild.path.Path(filename)

        if self._file_name.exists():
            with open(self._file_name, 'rb') as f:
                unpickler = fbuild.db.backend.Unpickler(self._ctx, f)
                try:
                    data = unpickler.load()
                except AttributeError:
                    # Likely a moved member. Just start clean!
                    super()._connect()
                    return

                if len(data) == 6:
                    # This was created before DB versioning was introduced. Use
                    # a fake version.
                    data = (self._NULL_VERSION,) + data

                self._version, self._functions, self._function_calls, \
                    self._files, self._call_files, self._external_srcs, \
                    self._external_dsts = data
        else:
            super()._connect()


    def close(self):
        """Save the database to the file."""

        f = io.BytesIO()
        pickler = fbuild.db.backend.Pickler(self._ctx, f)

        pickler.dump((
            self._LATEST_VERSION,
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
