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
