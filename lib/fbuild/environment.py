import pickle
import threading
import collections

from fbuild import ConfigFailed
from fbuild.functools import bind_args, import_function
from fbuild.record import Record

# ------------------------------------------------------------------------------

class _FunctionStack(threading.local, collections.UserList):
    pass

# ------------------------------------------------------------------------------

class Environment:
    '''
    Environment objects simplify the interface for the configuration by
    exposing routines that allow you to treat items as attributes, or
    automatically memoize results.
    '''

    __slots__ = (
        '_builder_state',
        '_runtime_state',
        '_function_state',
        '_thread_stack',
    )

    def __init__(self):
        # The _builder_state persistently caches the results of the function
        # over multiple python sessions.
        self._builder_state = {}

        # The _runtime_state memory caches the results of the function for this
        # python session.
        self._runtime_state = {}

        # The _function_state is used to determine if the function has changed
        # from the last python session. It stores a hash of the last function
        # code that we'll compare to the current value and a list of
        # dependencies. If it has changed, then throw away the cached values as
        # well as the function states of all the functions that depend on this
        # function.
        self._function_state = {}

        # The thread stack is used so we can figure out which functions depend
        # on other cached functions. We can then use this to rerun those
        # functions when their dependencies change.
        self._thread_stack = _FunctionStack()

    def cache(self, function, *args, **kwargs):
        '''
        Return the cached value or compute and store it in the cache.

        Function will be passed the environment in case it has other
        subfunctions to configure.
        '''
        return self._cache(self._builder_state, function, *args, **kwargs)

    def run(self, function, *args, **kwargs):
        return self._cache(self._runtime_state, function, *args, **kwargs)

    # -------------------------------------------------------------------------

    def __getstate__(self):
        # We don't want to cache most exceptions, as we want them recomputed
        # on the next run.
        builder_state = {}
        for key, value in self._builder_state.items():
            value = [v for v in value
                if isinstance(v[1], ConfigFailed)
                or not isinstance(v[1], Exception)]
            if value:
                builder_state[key] = value

        return {
            'builder_state': builder_state,
            'function_state': self._function_state,
        }

    def __setstate__(self, state):
        self._builder_state = state['builder_state']
        self._function_state = state['function_state']

        self._runtime_state = {}
        self._thread_stack = _FunctionStack()

        # Recursively clear the cached values of all the functions that
        # changed.
        visited_functions = {}
        def clean(function):
            # Exit early if we've already cleaned this function.
            try:
                return visited_functions[function]
            except KeyError:
                pass

            old_function_hash, dependencies = self._function_state[function]

            is_dirty = False
            for dep in dependencies:
                if clean(dep):
                    is_dirty = True

            if is_dirty:
                visited_functions[function] = True
                return True

            # Determine the hash of the function.
            if old_function_hash != self._function_hash(function):
                # This function or a dependency changed, so add it to the dirty list
                visited_functions[function] = True
                return True

            visited_functions[function] = False
            return False

        for function in list(self._function_state):
            clean(function)

        for function, is_dirty in visited_functions.items():
            if not is_dirty:
                continue

            # We want to recompute everything for this function, so just delete it.
            try:
                del self._function_state[function]
            except KeyError:
                pass

            # we're dirty from the last run, so remove ourselves from the builder cache

            key = '%s.%s' % (function.__module__, function.__name__)

            try:
                del self._builder_state[key]
            except KeyError:
                # Ack! after all that work we didn't actually have any
                # persistent data to clear out. So, then we're not actually
                # dirty.
                pass

    def _cache(self, cache, function, *args, **kwargs):
        function = import_function(function)

        # Add self to the arg list, then remove it so that it doesn't get
        # saved.
        bound_args = bind_args(function, args, kwargs)

        key = '%s.%s' % (function.__module__, function.__name__)

        # We need to figure out the function dependencies. We do this by
        # storing a stack on each thread, and each time the cached functions
        # calls cache, then we know that the first function has a dependency on
        # the called function. It needs to be thread specific so that multiple
        # threads can use the cache.
        if self._thread_stack:
            # if there are already values in the thread stack, that means that
            # another cached function called this function. So, add this
            # function to that function's dependencies.
            self._thread_stack[-1].add(function)

        # Try to see if we've called this function before.
        try:
            states = cache[key]
        except KeyError:
            pass
        else:
            # search the states for the args and kwargs
            for b, value in states:
                if bound_args == b:
                    # We found a cached builder state that has the same
                    # arguments. If the cached value is an exception, raise it.
                    # Otherwise, just return it.
                    if isinstance(value, Exception):
                        raise value
                    return value

        # We didn't find this function called with these arguments, so we'll
        # evaluate the expression. Before we can do that though, we must first
        # prepare the thread stack. First, look up the dependencies for this
        # function.
        try:
            deps = self._function_state[function][1]
        except KeyError:
            # No dependencies exist, so this must be the first time we called
            # this function. So, store both a new dependency set and a hash of
            # the function's code.
            deps = set()
            self._function_state[function] = self._function_hash(function), deps

        # Now, add the dependencies to the end of the stack so that if any of
        # the child functions use the cache they'll be added as a dependency.
        self._thread_stack.append(deps)

        # Finally, lets call this function.
        try:
            value = function(*args, **kwargs)
        except Exception as e:
            # cache the exception, store it in the cache, then reraise it
            value = e
            cache.setdefault(key, []).append((bound_args, value))
            raise e from e
        finally:
            self._thread_stack.pop()

        cache.setdefault(key, []).append((bound_args, value))

        return value

    def _function_hash(self, function):
        '''Hash the function's code and return it.'''

        return (
            function.__annotations__,
            function.__defaults__,
            function.__kwdefaults__,
            function.__code__.co_argcount,
            function.__code__.co_cellvars,
            function.__code__.co_code,

            # We can't include the constants as they might include code
            # objects, which aren't pickable.
            # function.__code__.co_consts,

            function.__code__.co_filename,
            function.__code__.co_flags,
            function.__code__.co_freevars,
            function.__code__.co_kwonlyargcount,
            function.__code__.co_name,
            function.__code__.co_names,
            function.__code__.co_nlocals,
            function.__code__.co_stacksize,
            function.__code__.co_varnames,
        )
