import inspect

# ------------------------------------------------------------------------------

def import_function(function):
    '''
    L{import_function} is a shortcut that will import and return L{function} if
    it is a I{str}. If not, then it is assumed that L{function} is callable,
    and is returned.
    '''

    if isinstance(function, str):
        m, f = function.rsplit('.', 1)
        return getattr(__import__(m, {}, {}, ['']), f)
    return function

def call(function, *args, **kwargs):
    '''
    L{call} is a shortcut that will call L{function} with the specified
    arguments. If L{function} is a I{str}, it is imported first. This
    eliminates the need to import the module directly.
    '''

    return import_function(function)(*args, **kwargs)

# ------------------------------------------------------------------------------

def bind_args(function, args, kwargs):
    '''
    Return the values of all the arguments bound to the names specified in the
    function.
    '''

    # Get the specification of the arguments for the function
    spec = inspect.getfullargspec(function)
    fn_args = spec.args
    fn_kwargs = spec.kwonlyargs
    varargs = spec.varargs is not None
    varkw = spec.varkw is not None

    # If there are no arguments, error out if extra ones were provided.
    if not fn_args and not fn_kwargs and not varargs and not varkw:
        if args or kwargs:
            raise TypeError(
                '%s.%s() takes no arguments (%d given)' % (
                    function.__module__,
                    function.__name__,
                    len(args) + len(kwargs)))
        else:
            return {}

    bound_args = {}

    # Copy the dictionary as we'll be popping items out of it
    kwargs = dict(kwargs)

    defaults = spec.defaults or []
    defcount = len(defaults)
    fn_argcount = len(fn_args)
    fn_kwargcount = len(fn_kwargs)
    fn_totalargs = fn_argcount + fn_kwargcount

    # Error out if we specified too many arguments and we aren't taking varargs
    if len(args) > fn_totalargs and not varargs:
        raise TypeError(
            '%s.%s() takes %s %d %spositional argument%s (%d given)' % (
                function.__module__,
                function.__name__,
                'at most' if defcount else 'exactly',
                fn_totalargs,
                '' if fn_kwargcount else 'non-keyword ',
                '' if fn_totalargs == 1 else 's',
                len(args)))

    new_args = list(args)

    # For each function argument, find the arg or kwarg it corresponds with
    argcount = 0
    for i, key in enumerate(fn_args):
        # First, check if we provide a kwarg for it
        try:
            value = kwargs.pop(key)
        except KeyError:
            # No kwarg, so see if we specified an argument
            if i < len(args):
                bound_args[key] = args[i]

            # no arg, so see if there's a default
            elif fn_argcount - i <= defcount:
                bound_args[key] = defaults[defcount - (fn_argcount - i)]
            else:
                # we didn't find an arg so break and error out later
                break
        else:
            # We found a kwarg for it, but if there are regular args, we got
            # the same argument twice, so error out.
            if i < len(args):
                raise TypeError(
                    '%s.%s() got multiple values for keyword argument %r' % (
                        function.__module__,
                        function.__name__,
                        key))

            bound_args[key] = value
        argcount += 1

    # If we didn't get enough arguments, error out
    if argcount + defcount < fn_argcount:
        raise TypeError(
            '%s.%s() takes %s %d %spositional argument%s (%d given)' % (
                function.__module__,
                function.__name__,
                'at least' if varargs or defaults else 'exactly',
                fn_totalargs,
                '' if fn_kwargcount else 'non-keyword ',
                '' if fn_totalargs == 1 else 's',
                len(args)))

    # If we take varargs, add them to the vararg name
    if varargs and argcount < len(args):
        bound_args[spec.varargs] = args[argcount:]

    # Now, add the function kwargs
    for key in fn_kwargs:
        try:
            bound_args[key] = kwargs.pop(key)
        except KeyError:
            # If no kwarg was specified, so see if there's a default argument
            try:
                bound_args[key] = spec.kwdefaults[key]
            except KeyError:
                # None found, so error out
                raise TypeError(
                    '%s.%s() needs keyword-only argument %s' %
                    (function.__module__, function.__name__, key))

    # If we take varkw, add them now
    if varkw:
        bound_args.update(kwargs)
    else:
        for key, value in kwargs.items():
            # if the key isn't in the fn_args, it's unknown
            if key not in fn_args:
                raise TypeError(
                    '%s() got an unexpected keyword argument %r' %
                    (function.__name__, key))

            bound_args[key] = value

    return bound_args
